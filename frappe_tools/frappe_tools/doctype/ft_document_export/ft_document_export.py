# Copyright (c) 2024, Maxim S and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.core.doctype.file.file import File
from frappe.model.document import Document
from frappe.utils.data import cint


class FTDocumentExport(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		doctype_type: DF.Link | None
		export_type: DF.Literal["JSON"]
	# end: auto-generated types
 
	def get_backup_name(self):
		from datetime import datetime
		now = datetime.now()
		date_time = now.strftime("%Y-%d-%m %H:%M:%S")
		return  f"{date_time} {self.doctype_type}.{self.export_type.lower()}"

	def get_all_data(self):
		# Отримуємо список усіх DocType
		doctypes = frappe.get_all(self.doctype_type, fields=["*"])

		# Збираємо дані про кожен DocType
		doctype_data = {}
		doctype_data.update({	"table": self.doctype_type,
                       			"rows":doctypes
                          })

		# Зберігаємо зібрані дані у файл JSON
		return frappe.as_json(doctype_data, ensure_ascii=False)

	def upload_file(self, content, is_private=1):
		"""
		Завантажити файл у Frappe.
		
		:param file_path: Локальний шлях до файлу.
		:param doctype: DocType, до якого прикріплюється файл (опціонально).
		:param docname: Ім'я документа, до якого прикріплюється файл (опціонально).
		:param is_private: Чи буде файл приватним (1 - приватний, 0 - публічний).
		:return: Створений документ файлу.
		"""
		filename = self.get_backup_name()
		# Створюємо документ File
  
		file_doc = frappe.get_doc(
			{
				"doctype": "File",
				"attached_to_doctype": self.doctype,
				"attached_to_name": self.name,
				# "attached_to_field": fieldname,
				"folder": "Home",
				"file_name": filename,
				# "file_url": file_url,
				"is_private": cint(is_private),
				"content": content,
			}
		).save(ignore_permissions=1)
		return file_doc

@frappe.whitelist()
def make_backup(docname):
    doc: FTDocumentExport = frappe.get_doc("FT Document Export", docname)
    data = doc.get_all_data()
    doc.upload_file(data)