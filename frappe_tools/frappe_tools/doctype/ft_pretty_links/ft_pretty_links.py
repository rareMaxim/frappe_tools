# Copyright (c) 2024, Maxim S and contributors
# For license information, please see license.txt

# import frappe
from frappe import _
import frappe
from frappe.desk.search import LinkSearchResults
from frappe.model.document import Document
from frappe.utils.data import cstr, unique


class FTPrettyLinks(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF

        doctype_ref: DF.Link | None
        enabled: DF.Check
        parse_title_for_links: DF.Check
        show_name_in_description: DF.Check
    # end: auto-generated types

    pass


def build_for_autosuggest_origin(
    res: list[tuple], doctype: str
) -> list[LinkSearchResults]:
    def to_string(parts):
        return ", ".join(
            unique(
                _(cstr(part)) if meta.translated_doctype else cstr(part)
                for part in parts
                if part
            )
        )

    results = []
    meta = frappe.get_meta(doctype)
    if meta.show_title_field_in_link:
        for item in res:
            item = list(item)
            if len(item) == 1:
                item = [item[0], item[0]]
            label = item[1]  # use title as label
            item[1] = item[0]  # show name in description instead of title

            if len(item) >= 3 and item[2] == label:
                # remove redundant title ("label") value
                del item[2]

            autosuggest_row = {"value": item[0], "description": to_string(item[1:])}
            if label:
                autosuggest_row["label"] = label

            results.append(autosuggest_row)
    else:
        results.extend(
            {"value": item[0], "description": to_string(item[1:])} for item in res
        )

    return results


def check_pretty_enabled(doctype: str) -> bool:
    """Check if pretty links are enabled for a doctype."""
    return (
        frappe.db.count(
            dt="FT Pretty Links", filters={"enabled": 1, "doctype_ref": doctype}
        )
        > 0
    )


def build_for_autosuggest(res: list[tuple], doctype: str) -> list[LinkSearchResults]:
    pretty_enabled = check_pretty_enabled(doctype)
    if pretty_enabled:
        return build_for_autosuggest_pretty(res, doctype)
    else:
        return build_for_autosuggest_origin(res, doctype)


def build_for_autosuggest_pretty(
    res: list[tuple], doctype: str
) -> list[LinkSearchResults]:
    def to_string(parts):
        return ", ".join(
            unique(
                _(cstr(part)) if meta.translated_doctype else cstr(part)
                for part in parts
                if part
            )
        )

    results = []
    pretty_enabled = check_pretty_enabled(doctype)
    if not pretty_enabled:
        return build_for_autosuggest_origin(res, doctype)
    config: FTPrettyLinks = frappe.get_last_doc(
        doctype="FT Pretty Links", filters={"enabled": 1, "doctype_ref": doctype}
    )
    meta = frappe.get_meta(doctype)
    if meta.show_title_field_in_link:
        for item in res:
            item = list(item)
            if len(item) == 1:
                item = [item[0], item[0]]
            label = item[1]  # use title as label
            if config.show_name_in_description == 1:
                item[1] = item[0]  # show name in description instead of title
            else:
                del item[2]
                del item[1]

            if len(item) >= 3 and item[2] == label:
                # remove redundant title ("label") value
                del item[2]
            print(item)
            autosuggest_row = {"value": item[0], "description": to_string(item[1:])}
            if label:
                autosuggest_row["label"] = label

            results.append(autosuggest_row)
    else:
        results.extend(
            {"value": item[0], "description": to_string(item[1:])} for item in res
        )

    return results
