// Copyright (c) 2024, Maxim S and contributors
// For license information, please see license.txt

frappe.ui.form.on("FT Document Export", {
    refresh(frm) {
        frm.page.set_primary_action("Export", () => {
            frappe.call({
                method: "frappe_tools.frappe_tools.doctype.ft_document_export.ft_document_export.make_backup",
                args: {
                    docname: frm.doc.name,
                },
                callback: function (r) {
                    frm.reload_doc()
                },
            });
        });
    },
    go(frm) {

    }
});
