# Copyright (c) 2025, Maxim S and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document


class FTTableClear(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		doctype_name: DF.Link | None
	# end: auto-generated types

@frappe.whitelist()
def get_count(doctype_name):
	return frappe.db.count(doctype_name) or 0

@frappe.whitelist()
def clean_up(doctype_name):
	frappe.db.delete(doctype_name)
