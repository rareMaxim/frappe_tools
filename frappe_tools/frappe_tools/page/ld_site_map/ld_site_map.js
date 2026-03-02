// Copyright (c) 2026, Maxim S and contributors
// For license information, please see license.txt

frappe.pages["ld-site-map"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Site Structure Map"),
		single_column: true,
	});

	// ── HTML skeleton ──────────────────────────────────────────────────────
	$(page.body).html(frappe.render_template("ld_site_map", {}));

	page.set_primary_action(__("Refresh"), load_data, "refresh");

	// ── State ──────────────────────────────────────────────────────────────
	let current_filter = "all";
	let search_query = "";
	let entity_paths_map = {};

	// ── Data loading ───────────────────────────────────────────────────────
	function load_data() {
		$(page.body)
			.find(".ld-apps")
			.html(
				`<div class="text-center text-muted p-5" style="font-size:1rem">
				${__("Loading site structure...")}
			</div>`
			);
		frappe.call({
			method: "frappe_tools.frappe_tools.page.ld_site_map.ld_site_map.get_site_structure",
			callback(r) {
				if (r.message) {
					render_summary(r.message.summary, r.message.site);
					render_apps(r.message.apps);
					apply_filters();
				}
			},
		});
	}

	// ── Render: Summary ────────────────────────────────────────────────────
	function render_summary(s, site) {
		const pct = s.total_entities ? Math.round((s.lost_entities / s.total_entities) * 100) : 0;
		$(page.body).find(".ld-summary").html(`
			<div class="ld-stat">
				<div class="ld-stat-value">${frappe.utils.escape_html(site)}</div>
				<div class="ld-stat-label">${__("Site")}</div>
			</div>
			<div class="ld-stat">
				<div class="ld-stat-value">${s.total_apps}</div>
				<div class="ld-stat-label">${__("Apps")}</div>
			</div>
			<div class="ld-stat s-warn">
				<div class="ld-stat-value">${s.apps_with_desktop_icon}</div>
				<div class="ld-stat-label">${__("With desktop icon")}</div>
			</div>
			<div class="ld-stat">
				<div class="ld-stat-value">${s.total_entities}</div>
				<div class="ld-stat-label">${__("Total Entities")}</div>
			</div>
			<div class="ld-stat s-success">
				<div class="ld-stat-value">${s.accessible_entities}</div>
				<div class="ld-stat-label">${__("Accessible via UI")}</div>
			</div>
			<div class="ld-stat s-danger">
				<div class="ld-stat-value">${s.lost_entities}
					<span style="font-size:1rem;font-weight:400">(${pct}%)</span>
				</div>
				<div class="ld-stat-label">${__("Not accessible (lost)")}</div>
			</div>
		`);
	}

	// ── Render: App cards ──────────────────────────────────────────────────
	function render_apps(apps) {
		const $container = $(page.body).find(".ld-apps").empty();
		const cards_html = [];

		apps.forEach((app) => {
			const icon_badge = app.has_desktop_icon
				? `<span class="ld-badge b-green">🖥 ${__("has icon")}</span>`
				: `<span class="ld-badge b-gray">${__("no icon")}</span>`;

			const lost_badge =
				app.lost_entities > 0
					? `<span class="ld-badge b-red">⚠ ${app.lost_entities} ${__("lost")}</span>`
					: `<span class="ld-badge b-green">✓ ${__("all accessible")}</span>`;

			const modules_html = app.modules
				.map((mod) => {
					const chips = mod.entities
						.map((ent) => {
							const cls = [
								"ld-entity",
								ent.in_workspace ? "accessible" : "lost",
								ent.issingle ? "is-single" : "",
								ent.is_virtual ? "is-virtual" : "",
							]
								.filter(Boolean)
								.join(" ");

							const tags = [
								ent.issingle ? __("Single") : "",
								ent.is_virtual ? __("Virtual") : "",
								ent.custom ? __("Custom") : "",
							]
								.filter(Boolean)
								.join(", ");

							const type_badge_map = {
								DocType: `<span class="ld-badge b-blue">${__("DocType")}</span>`,
								Page: `<span class="ld-badge b-green">${__("Page")}</span>`,
								Report: `<span class="ld-badge b-purple">${__("Report")}</span>`,
								"Child Table": `<span class="ld-badge b-orange">${__(
									"Child Table"
								)}</span>`,
							};
							const type_badge = type_badge_map[ent.type] || "";

							entity_paths_map[ent.name] = ent.paths;

							return `<span
								class="${cls}"
								data-name="${frappe.utils.escape_html(ent.name)}"
								data-type="${frappe.utils.escape_html(ent.type)}"
								data-accessible="${ent.in_workspace ? 1 : 0}"
								title="${tags}"
							>${type_badge} ${frappe.utils.escape_html(ent.name)}</span>`;
						})
						.join("");

					return `
					<div class="ld-module"
						data-module="${frappe.utils.escape_html(mod.name.toLowerCase())}">
						<div class="ld-module-header">
							${frappe.utils.escape_html(mod.name)}
							<span class="ld-module-stats">
								${__("{0} accessible / {1} lost", [mod.accessible, mod.lost])}
							</span>
						</div>
						<div class="ld-entities">${chips}</div>
					</div>`;
				})
				.join("");

			const card_html = `
				<div class="ld-app-card" data-app="${frappe.utils.escape_html(app.name)}">
					<div class="ld-app-header">
						<span class="ld-app-toggle">▾</span>
						<span class="ld-app-name">${frappe.utils.escape_html(app.name)}</span>
						${icon_badge}
						${lost_badge}
						<span class="ld-badge b-gray">${app.total_entities} ${__("Entities")}</span>
					</div>
					<div class="ld-app-body">
						${modules_html || `<div class="text-muted" style="font-size:0.85rem">${__("No Entities")}</div>`}
					</div>
				</div>`;
			cards_html.push(card_html);
		});

		$container.html(cards_html.join(""));
	}

	// ── Filters ────────────────────────────────────────────────────────────
	function apply_filters() {
		const is_filtering = current_filter !== "all" || search_query !== "";

		$(page.body)
			.find(".ld-entity")
			.each(function () {
				const $chip = $(this);
				const name = ($chip.data("name") || "").toLowerCase();
				const accessible = !!parseInt($chip.data("accessible"));

				let show = true;
				if (current_filter === "lost" && accessible) show = false;
				if (current_filter === "accessible" && !accessible) show = false;
				if (search_query && !name.includes(search_query)) show = false;

				$chip.toggleClass("ld-hide", !show);
			});

		// hide modules with no visible chips (only when filtering)
		$(page.body)
			.find(".ld-module")
			.each(function () {
				if (!is_filtering) {
					$(this).removeClass("ld-hide");
					return;
				}
				const has_visible = $(this).find(".ld-entity:not(.ld-hide)").length > 0;
				$(this).toggleClass("ld-hide", !has_visible);
			});

		// hide app cards with no visible modules (only when filtering)
		$(page.body)
			.find(".ld-app-card")
			.each(function () {
				if (!is_filtering) {
					$(this).removeClass("ld-hide");
					return;
				}
				const has_visible = $(this).find(".ld-module:not(.ld-hide)").length > 0;
				$(this).toggleClass("ld-hide", !has_visible);
			});
	}

	// ── Entity chip click → show paths dialog ─────────────────────────────
	$(page.body).on("click", ".ld-entity", function () {
		const name = $(this).data("name");
		const type = $(this).data("type");
		const accessible = !!parseInt($(this).data("accessible"));
		const paths = entity_paths_map[name] || [];

		const is_child_table = type === "Child Table";

		let route = [];
		let open_label = "";
		if (type === "DocType") {
			route = ["List", name];
			open_label = __("Open DocType");
		} else if (type === "Page") {
			route = ["page", name];
			open_label = __("Open Page");
		} else if (type === "Report") {
			route = ["query-report", name];
			open_label = __("Open Report");
		}

		let open_btn;
		if (is_child_table) {
			// Extract parent DocType name from path strings like "Parent: Foo" or "Parent (custom field): Foo"
			const parent_names = paths.map((p) => p.replace(/^[^:]+:\s*/, ""));
			const parent_btns = parent_names
				.slice(0, 4)
				.map((pname) => {
					const pr = `'List', '${pname.replace(/'/g, "\\'")}'`;
					return `<button class="btn btn-sm btn-primary"
						onclick="frappe.set_route(${pr}); cur_dialog && cur_dialog.hide()">
						↗ ${frappe.utils.escape_html(pname)}
					</button>`;
				})
				.join("");
			const edit_route = `'Form', 'DocType', '${name.replace(/'/g, "\\'")}'`;
			const edit_btn = `<button class="btn btn-sm btn-default"
				onclick="frappe.set_route(${edit_route}); cur_dialog && cur_dialog.hide()">
				✏ ${__("Edit DocType")}
			</button>`;
			open_btn = `<div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap">${parent_btns}${edit_btn}</div>`;
		} else {
			const route_str = route.map((r) => `'${r.replace(/'/g, "\\'")}'`).join(", ");
			open_btn = `<div style="margin-top:14px">
				<button class="btn btn-sm btn-primary"
					onclick="frappe.set_route(${route_str}); cur_dialog && cur_dialog.hide()">
					↗ ${open_label}
				</button>
			</div>`;
		}

		if (!accessible) {
			frappe.msgprint({
				title: name,
				message: `<div>
					<div style="color:var(--red-600);margin-bottom:6px">
						⚠ ${
							is_child_table
								? __("Not used in any parent DocType — orphan child table.")
								: __(
										"Not accessible via UI — not found in any Workspace or Sidebar."
								  )
						}
					</div>
					<div style="color:var(--text-muted);font-size:0.85rem">
						${__("You can still open it directly:")}
					</div>
					${open_btn}
				</div>`,
				indicator: "red",
			});
			return;
		}

		const paths_html = paths
			.map((p) => `<li style="margin:4px 0">📍 ${frappe.utils.escape_html(p)}</li>`)
			.join("");

		frappe.msgprint({
			title: name,
			message: `<div>
				<div style="color:var(--green-700);margin-bottom:8px">
					✓ ${is_child_table ? __("Used in parent DocType(s)") : __("Accessible via UI")}
				</div>
				<strong>${is_child_table ? __("Parent DocTypes") : __("Path")}:</strong>
				<ul style="margin:6px 0 0 0;padding-left:16px">${paths_html}</ul>
				${open_btn}
			</div>`,
			indicator: "green",
		});
	});

	// ── Toggle collapse ────────────────────────────────────────────────────
	$(page.body).on("click", ".ld-app-header", function () {
		$(this).closest(".ld-app-card").toggleClass("collapsed");
	});

	// ── Filter buttons ─────────────────────────────────────────────────────
	$(page.body).on("click", ".ld-filter-btn", function () {
		current_filter = $(this).data("filter");
		$(page.body).find(".ld-filter-btn").removeClass("active");
		$(this).addClass("active");
		apply_filters();
	});

	// ── Search ─────────────────────────────────────────────────────────────
	$(page.body).on(
		"input",
		".ld-search",
		frappe.utils.debounce(function () {
			search_query = $(this).val().toLowerCase();
			apply_filters();
		}, 300)
	);

	// ── Init ───────────────────────────────────────────────────────────────
	load_data();
};
