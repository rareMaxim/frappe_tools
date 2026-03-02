# Copyright (c) 2026, Maxim S and contributors
# For license information, please see license.txt

from collections import defaultdict
from typing import Literal, TypedDict

import frappe

ENTITY_TYPE = Literal["DocType", "Page", "Report"]


class Entity(TypedDict):
	type: ENTITY_TYPE
	name: str
	module: str
	custom: bool
	# DocType-specific
	issingle: bool
	is_virtual: bool


@frappe.whitelist()
def get_site_structure() -> dict:
	"""
	Collects site structure:
	- installed apps and their Desktop Icons
	- all DocTypes per module per app
	- for each DocType: is it accessible via UI, and through which Workspaces
	"""
	frappe.only_for("System Manager")

	linked_entities = get_linked_entities()
	all_entities = get_all_entities()

	all_entities_by_module = defaultdict(list)
	for ent in all_entities:
		all_entities_by_module[ent["module"]].append(ent)

	# --- Desktop Icons ---
	desktop_icons = frappe.get_all(
		"Desktop Icon",
		fields=["name", "app", "module_name", "hidden"],
	)
	di_by_app: dict[str, list[dict]] = {}
	for di in desktop_icons:
		app = di.get("app") or di.get("module_name") or ""
		di_by_app.setdefault(app, []).append(di)

	# --- Build per-app structure ---
	installed_apps: list[str] = frappe.get_installed_apps()

	apps = []
	for app_name in installed_apps:
		# Query Module Def directly — more reliable than frappe.local.module_app
		app_modules = frappe.get_all(
			"Module Def",
			filters={"app_name": app_name},
			pluck="name",
			order_by="name asc",
		)
		app_icons = di_by_app.get(app_name, [])

		modules = []
		for module_name in app_modules:
			entities_in_module = all_entities_by_module.get(module_name, [])
			if not entities_in_module:
				continue

			ent_list = []
			for ent in entities_in_module:
				ent_list.append(
					{
						"type": ent["type"],
						"name": ent["name"],
						"issingle": ent.get("issingle", False),
						"is_virtual": ent.get("is_virtual", False),
						"custom": ent.get("custom", False),
						"in_workspace": f"{ent['type']}:{ent['name']}" in linked_entities,
						# list of workspaces/sidebars where this DT is linked
						"paths": linked_entities.get(f"{ent['type']}:{ent['name']}", []),
					}
				)

			modules.append(
				{
					"name": module_name,
					"entities": ent_list,
					"total": len(ent_list),
					"accessible": sum(1 for d in ent_list if d["in_workspace"]),
					"lost": sum(1 for d in ent_list if not d["in_workspace"]),
				}
			)

		total_ent = sum(m["total"] for m in modules)
		accessible_ent = sum(m["accessible"] for m in modules)

		apps.append(
			{
				"name": app_name,
				"has_desktop_icon": bool(app_icons),
				"desktop_icons": [{"name": di["name"], "hidden": bool(di.get("hidden"))} for di in app_icons],
				"modules": modules,
				"total_entities": total_ent,
				"accessible_entities": accessible_ent,
				"lost_entities": total_ent - accessible_ent,
			}
		)

	summary = {
		"total_apps": len(apps),
		"apps_with_desktop_icon": sum(1 for a in apps if a["has_desktop_icon"]),
		"total_entities": sum(a["total_entities"] for a in apps),
		"accessible_entities": sum(a["accessible_entities"] for a in apps),
		"lost_entities": sum(a["lost_entities"] for a in apps),
	}

	return {
		"site": frappe.local.site,
		"generated_at": frappe.utils.now_datetime().isoformat(),
		"summary": summary,
		"apps": apps,
	}


def get_linked_entities() -> dict[str, list[str]]:
	"""
	Returns a dict of all entities linked in UI, in the format:
	{ "DocType:User": ["Workspace:...", "Sidebar:..."], ... }
	"""
	paths_set: dict[str, set[str]] = {}

	# --- Workspace Links (left sidebar) ---
	if frappe.db.exists("DocType", "Workspace Link"):
		links = frappe.get_all(
			"Workspace Link",
			fields=["link_type", "link_to", "parent"],
		)
		for lnk in links:
			if not lnk.link_to:
				continue
			key = f"{lnk.link_type}:{lnk.link_to}"
			paths_set.setdefault(key, set()).add(f"{frappe._('Workspace')}: {lnk.parent}")

	# --- Workspace Shortcuts (main content) ---
	if frappe.db.exists("DocType", "Workspace Shortcut"):
		shortcuts = frappe.get_all(
			"Workspace Shortcut",
			fields=["type", "link_to", "parent"],
		)
		for sc in shortcuts:
			if not sc.link_to:
				continue
			key = f"{sc.type}:{sc.link_to}"
			paths_set.setdefault(key, set()).add(f"{frappe._('Shortcut')}: {sc.parent}")

	# --- Custom Workspace Sidebar Items (e.g. orange_inventory style) ---
	if frappe.db.exists("DocType", "Workspace Sidebar Item"):
		items = frappe.get_all(
			"Workspace Sidebar Item",
			fields=["link_type", "link_to", "parent"],
		)
		for item in items:
			if not item.link_to:
				continue
			key = f"{item.link_type}:{item.link_to}"
			paths_set.setdefault(key, set()).add(f"{frappe._('Sidebar')}: {item.parent}")

	# --- Desktop Icons ---
	if frappe.db.exists("DocType", "Desktop Icon"):
		desktop_icons = frappe.get_all(
			"Desktop Icon",
			fields=["link_type", "link_to", "name"],
		)
		for di in desktop_icons:
			if not di.link_to:
				continue
			# Desktop Icons can link to Workspace Sidebars, which are not entities
			if di.link_type == "Workspace Sidebar":
				continue
			key = f"{di.link_type}:{di.link_to}"
			paths_set.setdefault(key, set()).add(f"{frappe._('Desktop Icon')}: {di.name}")

	# --- Child Tables used via DocField (Table / Table MultiSelect) ---
	table_fields = frappe.get_all(
		"DocField",
		filters={"fieldtype": ["in", ["Table", "Table MultiSelect"]]},
		fields=["parent", "options"],
	)
	for tf in table_fields:
		if not tf.options:
			continue
		key = f"Child Table:{tf.options}"
		paths_set.setdefault(key, set()).add(f"{frappe._('Parent')}: {tf.parent}")

	# --- Child Tables used via Custom Field ---
	if frappe.db.exists("DocType", "Custom Field"):
		custom_table_fields = frappe.get_all(
			"Custom Field",
			filters={"fieldtype": ["in", ["Table", "Table MultiSelect"]]},
			fields=["dt", "options"],
		)
		for ctf in custom_table_fields:
			if not ctf.options:
				continue
			key = f"Child Table:{ctf.options}"
			paths_set.setdefault(key, set()).add(f"{frappe._('Parent')} (custom field): {ctf.dt}")

	return {k: list(v) for k, v in paths_set.items()}


def get_all_entities() -> list[Entity]:
	"""Returns a list of all queryable entities."""
	entities: list[Entity] = []

	# --- DocTypes ---
	doctypes = frappe.get_all(
		"DocType",
		filters={"istable": 0},
		fields=["name", "module", "issingle", "is_virtual", "custom"],
	)
	for dt in doctypes:
		entities.append(
			{
				"type": "DocType",
				"name": dt.name,
				"module": dt.module,
				"issingle": bool(dt.issingle),
				"is_virtual": bool(dt.is_virtual),
				"custom": bool(dt.custom),
			}
		)

	# --- Child Tables ---
	child_tables = frappe.get_all(
		"DocType",
		filters={"istable": 1},
		fields=["name", "module", "custom"],
	)
	for ct in child_tables:
		entities.append(
			{
				"type": "Child Table",
				"name": ct.name,
				"module": ct.module,
				"issingle": False,
				"is_virtual": False,
				"custom": bool(ct.custom),
			}
		)

	# --- Pages ---
	pages = frappe.get_all(
		"Page",
		fields=["name", "module"],
	)
	for p in pages:
		entities.append(
			{
				"type": "Page",
				"name": p.name,
				"module": p.module,
				"issingle": False,
				"is_virtual": False,
				"custom": False,  # Pages don't have a "custom" field
			}
		)

	# --- Reports ---
	reports = frappe.get_all(
		"Report",
		fields=["name", "module", "is_standard"],
	)
	for r in reports:
		entities.append(
			{
				"type": "Report",
				"name": r.name,
				"module": r.module,
				"issingle": False,
				"is_virtual": False,
				"custom": r.is_standard == "No",
			}
		)

	return entities
