# Copyright (c) 2024, Maxim S and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.search import LinkSearchResults, search_widget
from frappe.utils.caching import redis_cache
from frappe.utils.data import cstr, unique


@frappe.whitelist()
def search_link(
	doctype: str,
	txt: str,
	query: str | None = None,
	filters: str | dict | list | None = None,
	page_length: int = 10,
	searchfield: str | None = None,
	reference_doctype: str | None = None,
	ignore_user_permissions: bool = False,
	*,
	link_fieldname: str | None = None,
) -> list[LinkSearchResults]:
	results = search_widget(
		doctype,
		txt.strip(),
		query,
		searchfield=searchfield,
		page_length=page_length,
		filters=filters,
		reference_doctype=reference_doctype,
		ignore_user_permissions=ignore_user_permissions,
		link_fieldname=link_fieldname,
	)
	config = get_pretty_config(doctype)
	if config:
		return build_pretty_results(results, doctype, config)
	from frappe.desk.search import build_for_autosuggest

	return build_for_autosuggest(results, doctype=doctype)


@redis_cache(ttl=60)
def get_pretty_config(doctype: str) -> dict | None:
	"""Повертає конфіг FT Pretty Links або None. Кешується 60с у Redis."""
	rows = frappe.get_all(
		"FT Pretty Links",
		filters={"enabled": 1, "doctype_ref": doctype},
		fields=["show_name_in_description", "resolve_search_links", "parse_title_for_links"],
		limit=1,
	)
	return rows[0] if rows else None


def build_pretty_results(
	res: list[tuple], doctype: str, config: dict
) -> list[LinkSearchResults]:
	meta = frappe.get_meta(doctype)

	# Резолвити Link-поля у search_fields → {raw_id: title} для description
	# col_offset: 1 без title_field, 2 з title_field (Frappe вставляє його на позицію 1)
	col_offset = 2 if meta.show_title_field_in_link else 1
	search_field_map: dict[str, str] = (
		_resolve_search_field_titles(meta, res, col_offset)
		if config.get("resolve_search_links")
		else {}
	)

	def to_str(parts):
		resolved = (
			search_field_map.get(cstr(p), _(cstr(p)) if meta.translated_doctype else cstr(p))
			for p in parts
			if p
		)
		return ", ".join(unique(resolved))

	if not meta.show_title_field_in_link:
		# DocType без title_field — стандартна поведінка
		return [
			{"value": item[0], "description": to_str(item[1:]), "label": cstr(item[0])}
			for item in res
		]

	# parse_title_for_links: резолвити linked title якщо title_field є Link-полем
	link_title_map: dict[str, str] = {}
	if config.get("parse_title_for_links"):
		link_title_map = _resolve_link_titles(meta)

	results = []
	for item in res:
		item = list(item)
		if len(item) == 1:
			item = [item[0], item[0]]

		raw_title = item[1]  # значення title_field

		# Визначити label: резолвлений linked title або звичайний title
		label = link_title_map.get(raw_title) or (
			_(raw_title) if meta.translated_doctype else raw_title
		)

		if config.get("show_name_in_description"):
			# label = title, description = name (ID) + resolved search fields
			item[1] = item[0]
			if len(item) >= 3 and item[2] == raw_title:
				del item[2]
			description = to_str(item[1:])
		else:
			# label = title, description = resolved search fields (name/ID прихований)
			# Фільтруємо raw_title щоб не дублювати значення title_field з label
			desc_parts = [p for p in item[2:] if p != raw_title]
			description = to_str(desc_parts)

		row: LinkSearchResults = {"value": item[0], "description": description}
		if label:
			row["label"] = label
		results.append(row)

	return results


def _resolve_search_field_titles(meta, res: list[tuple], col_offset: int) -> dict[str, str]:
	"""
	Для Link-типу полів у search_fields повертає словник {raw_id: title}.

	col_offset — з якої колонки починаються search_fields у кортежах res:
	  1 якщо DocType без title_field, 2 якщо з title_field.

	Приклад: Employee з search_fields="employee_name,job_offer"
	де job_offer — Link→Job Offer з title_field="job_title":
	→ {"POS-2025-00008": "Старший розробник", ...}
	"""
	search_fields = [f.strip() for f in (meta.search_fields or "").split(",") if f.strip()]
	result_map: dict[str, str] = {}

	for i, field_name in enumerate(search_fields):
		col_idx = col_offset + i
		field_meta = meta.get_field(field_name)
		if not field_meta or field_meta.fieldtype != "Link" or not field_meta.options:
			continue

		linked_meta = frappe.get_meta(field_meta.options)
		if not linked_meta.title_field:
			continue

		unique_ids = {
			item[col_idx]
			for item in res
			if len(item) > col_idx and item[col_idx]
		}
		if not unique_ids:
			continue

		rows = frappe.get_all(
			field_meta.options,
			filters={"name": ["in", list(unique_ids)]},
			fields=["name", linked_meta.title_field],
		)
		for row in rows:
			if row.get(linked_meta.title_field):
				result_map[row["name"]] = row[linked_meta.title_field]

	return result_map


def _resolve_link_titles(meta) -> dict[str, str]:
	"""
	Якщо title_field DocType є Link-полем, повертає словник {linked_name: linked_title}.

	Приклад: DocType "Employee" з title_field="department" (Link→Department),
	де Department має title_field="department_name":
	→ {"HR": "Human Resources", "FIN": "Finance", ...}
	"""
	tf = meta.get_field(meta.title_field)
	if not tf or tf.fieldtype != "Link" or not tf.options:
		return {}

	linked_meta = frappe.get_meta(tf.options)
	if not linked_meta.show_title_field_in_link or not linked_meta.title_field:
		return {}

	rows = frappe.get_all(
		tf.options,
		fields=["name", linked_meta.title_field],
		limit=0,
	)
	return {
		r["name"]: r[linked_meta.title_field]
		for r in rows
		if r.get(linked_meta.title_field)
	}
