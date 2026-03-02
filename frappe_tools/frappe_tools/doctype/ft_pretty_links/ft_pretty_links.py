# Copyright (c) 2024, Maxim S and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FTPrettyLinks(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		doctype_ref: DF.Link | None
		enabled: DF.Check
		parse_title_for_links: DF.Check
		resolve_search_links: DF.Check
		show_name_in_description: DF.Check
	# end: auto-generated types

	def on_update(self):
		_clear_config_cache()

	def after_delete(self):
		_clear_config_cache()


def _clear_config_cache():
	from frappe_tools.frappe_tools.doctype.ft_pretty_links.search import get_pretty_config

	get_pretty_config.clear_cache()
