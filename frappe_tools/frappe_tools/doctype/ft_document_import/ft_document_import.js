// Copyright (c) 2024, Maxim S and contributors
// For license information, please see license.txt

function MakeExportButton(frm) {
    frm.page.set_primary_action("Import", () => {
        frappe.call({
            method: "frappe_tools.frappe_tools.doctype.ft_document_import.ft_document_import.restore_backup",
            args: {
                docname: frm.doc.name,
            },
            callback: function (r) {
                frm.reload_doc()
            },
        });
    });
}

frappe.ui.form.on("FT Document Import", {
    refresh(frm) {
        MakeExportButton(frm);
    },

});
