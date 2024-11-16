# Copyright (c) 2024, Maxim S and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.core.doctype.file.file import File
from frappe.desk.doctype.bulk_update.bulk_update import show_progress
from frappe.model.document import Document


class FTDocumentImport(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		count: DF.Int
		doctype_type: DF.Link | None
		file: DF.Attach | None
	# end: auto-generated types

	def before_save(self):
		if not self.file:
			return
		json = self.get_json_file()
		self.count = len(json["rows"])
		self.doctype_type = json["table"]
	def get_title_field(self)->str:
		meta = frappe.get_meta(self.doctype_type)
		return meta.title_field or "name"

	def restore_backup(self):
		data = self.get_json_file()["rows"]
		for i, d in enumerate(data):
			doc_data = {"doctype": self.doctype_type}
			doc_data.update(d)
			doc_title = doc_data[self.get_title_field()]
			frappe.publish_progress(float(i) * 100 / self.count, title="Restore", description=doc_title)
			doc = frappe.get_doc(doc_data)
			try:
				doc.insert(	set_name=doc_data["name"],
               				ignore_links = True)
			except:
				pass
		pass

	def get_json_file(self)->File:
		file:File = frappe.get_last_doc("File", {"file_url": self.file})
		return json.loads(file.get_content()) 
	pass

@frappe.whitelist()
def restore_backup(docname):
	doc: FTDocumentImport = frappe.get_doc("FT Document Import", docname)
	data = doc.restore_backup()
