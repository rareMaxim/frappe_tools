# Copyright (c) 2026, Maxim S and contributors
# For license information, please see license.txt

import os
import shutil
import subprocess
import frappe
from frappe.model.document import Document
from frappe.utils import get_bench_path, now_datetime

class FTSystemCleanup(Document):
	@frappe.whitelist()
	def run_all_cleanups(self):
		self.last_cleanup = now_datetime()
		
		# Execute cleanups and capture stats
		logs_stats = self.clean_logs()
		cache_stats = self.clean_caches()
		git_stats = self.clean_git()
		
		# Update document fields
		self.logs_cleaned_size = logs_stats
		self.cache_cleared_size = cache_stats
		self.git_cleaned_size = git_stats
		
		self.save()
		frappe.db.commit()
		
		return {
			"logs": logs_stats,
			"cache": cache_stats,
			"git": git_stats
		}

	def clean_logs(self):
		bench_path = get_bench_path()
		cleaned_size = 0
		
		# 1. Main logs directory
		logs_dir = os.path.join(bench_path, "logs")
		cleaned_size += self._process_log_dir(logs_dir)
		
		# 2. Site-specific logs directories
		sites_dir = os.path.join(bench_path, "sites")
		if os.path.exists(sites_dir):
			for site in os.listdir(sites_dir):
				site_log_dir = os.path.join(sites_dir, site, "logs")
				if os.path.isdir(site_log_dir):
					cleaned_size += self._process_log_dir(site_log_dir)
					
		return self.format_size(cleaned_size)

	def _process_log_dir(self, log_dir):
		if not os.path.exists(log_dir):
			return 0
			
		cleaned_size = 0
		for filename in os.listdir(log_dir):
			file_path = os.path.join(log_dir, filename)
			if not os.path.isfile(file_path):
				continue
				
			# A. Remove rotated/archived logs
			if any(filename.endswith(f".{i}") for i in range(1, 50)) or filename.endswith(".log.gz"):
				try:
					cleaned_size += os.path.getsize(file_path)
					os.remove(file_path)
				except Exception as e:
					frappe.log_error(f"Error removing log file {file_path}: {str(e)}", "FT System Cleanup")
			
			# B. Truncate active logs if > 5MB
			elif filename.endswith(".log"):
				try:
					file_size = os.path.getsize(file_path)
					if file_size > 5 * 1024 * 1024: # 5MB
						# Truncate file
						with open(file_path, 'r+') as f:
							f.truncate(0)
						cleaned_size += file_size
				except Exception as e:
					frappe.log_error(f"Error truncating log file {file_path}: {str(e)}", "FT System Cleanup")
					
		return cleaned_size

	def clean_caches(self):
		# 1. Clear Redis
		try:
			frappe.cache.clear_all()
		except Exception as e:
			frappe.log_error(f"Error clearing Redis cache: {str(e)}", "FT System Cleanup")

		# 2. Clear __pycache__
		bench_path = get_bench_path()
		apps_dir = os.path.join(bench_path, "apps")
		cleaned_size = 0
		
		for root, dirs, files in os.walk(apps_dir):
			if "__pycache__" in dirs:
				pycache_path = os.path.join(root, "__pycache__")
				try:
					# Calculate size before removal
					for path, subdirs, subfiles in os.walk(pycache_path):
						for f in subfiles:
							fp = os.path.join(path, f)
							cleaned_size += os.path.getsize(fp)
					shutil.rmtree(pycache_path)
				except Exception as e:
					frappe.log_error(f"Error removing pycache {pycache_path}: {str(e)}", "FT System Cleanup")
					
		return self.format_size(cleaned_size)

	def clean_git(self):
		bench_path = get_bench_path()
		apps_dir = os.path.join(bench_path, "apps")
		
		# We'll just report success/fail as calculating git gc saving is complex
		apps = [d for d in os.listdir(apps_dir) if os.path.isdir(os.path.join(apps_dir, d))]
		success_count = 0
		
		for app in apps:
			app_path = os.path.join(apps_dir, app)
			if os.path.exists(os.path.join(app_path, ".git")):
				try:
					# Run git gc aggressively to free up space
					subprocess.run(["git", "gc", "--prune=now", "--quiet"], cwd=app_path, check=True)
					success_count += 1
				except Exception as e:
					frappe.log_error(f"Error running git gc in {app_path}: {str(e)}", "FT System Cleanup")
					
		return f"Optimized {success_count} apps"

	def format_size(self, size_bytes):
		if size_bytes == 0: return "0 B"
		size_name = ("B", "KB", "MB", "GB")
		import math
		i = int(math.floor(math.log(size_bytes, 1024)))
		p = math.pow(1024, i)
		s = round(size_bytes / p, 2)
		return f"{s} {size_name[i]}"
