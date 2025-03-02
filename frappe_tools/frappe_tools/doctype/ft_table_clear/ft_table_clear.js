// Copyright (c) 2025, Maxim S and contributors
// For license information, please see license.txt

function get_count(frm) {
    if (!frm.doc.doctype_name) return;
    frappe.call({
        method: "frappe_tools.frappe_tools.doctype.ft_table_clear.ft_table_clear.get_count",
        args: {
            "doctype_name": frm.doc.doctype_name
        },
        callback: function (r) {
            if (r.message) {
                frm.set_df_property("doctype_name", "description", "Count: " + r.message);
            }
        }
    });
}

frappe.ui.form.on("FT Table Clear", {
    refresh(frm) {
        get_count(frm);
    },
    doctype_name: function (frm) {
        get_count(frm)
    },

    clean_up(frm) {
        if (!frm.doc.doctype_name) return;
        frappe.call({
            method: "frappe_tools.frappe_tools.doctype.ft_table_clear.ft_table_clear.clean_up",
            args: {
                "doctype_name": frm.doc.doctype_name
            },
            callback: function (r) {
                get_count(frm)
            }
        });
    },
});