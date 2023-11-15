// Copyright (c) 2023, Maxim Sysoev and contributors
// For license information, please see license.txt

function update_count(frm) {
	frappe.call({
		method: 'frappe_tools.frappe_tools.doctype.ft_document_delete.ft_document_delete.get_count_doctype',
		args: {
			doctype: frm.doc.doc_type,
		},
		callback: function (r) {
			frm.set_value("count", r.message);
		}
	});
}
function get_docs_for_delete(frm) {
	return frappe.db.get_list(frm.doc.doc_type);
}
function run_batch_delete(frm) {
	frappe.call({
		method: 'frappe_tools.frappe_tools.doctype.ft_document_delete.ft_document_delete.delete_all_doctype',
		args: {
			doctype: frm.doc.doc_type,
			force: frm.doc.force,
			permanent: frm.doc.delete_permanently,
		},
		callback: function (r) {
			console.log(r);
		}
	});
}
frappe.ui.form.on("FT Document Delete", {
	refresh(frm) {
		update_count(frm)
	},
	doc_type(frm) {
		update_count(frm)
	},
	delete(frm) {
		run_batch_delete(frm)
	}
});
