# Copyright (c) 2023, Maxim Sysoev and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FTDocumentDelete(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        count: DF.Int
        delete_permanently: DF.Check
        doc_type: DF.Link | None
        force: DF.Check
        log: DF.Text | None
    # end: auto-generated types


@frappe.whitelist()
def get_count_doctype(doctype: str) -> int:
    """Returns the number of records in a doctype"""
    return frappe.db.count(doctype)


@frappe.whitelist()
def delete_all_doctype(doctype: str):
    config = frappe.get_single("FT Document Delete")
    docs = frappe.get_list(doctype, limit_page_length=20)
    print(docs)
    errors = []
    is_ok = True
    for doc in docs:
        try:
            frappe.delete_doc(
                doctype=doctype,
                name=doc.name,
                force=config.force,
                delete_permanently=config.delete_permanently,
            )

        except Exception as e:
            errors.append(str(e))
            is_ok = False

    return {"errors": errors, "is_ok": is_ok, "count": get_count_doctype(doctype)}
