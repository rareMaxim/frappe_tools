# Copyright (c) 2024, Maxim S and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class security_txt(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		acknowledgments: DF.Data | None
		contact_page: DF.Data | None
		csaf: DF.Date | None
		email: DF.Data | None
		encryption: DF.Data | None
		expires: DF.Datetime
		hiring: DF.Date | None
		phone: DF.Phone | None
		policy: DF.Data | None
		preferred_languages: DF.Data | None
	# end: auto-generated types

	pass
