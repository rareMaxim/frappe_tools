frappe.ui.form.on("FT System Cleanup", {
    refresh: function (frm) {
        frm.add_custom_button(__("Run Cleanup"), function () {
            frappe.confirm(__("Are you sure you want to run the system cleanup? This will clear caches and optimize git repositories."), function () {
                frm.call({
                    method: "run_all_cleanups",
                    doc: frm.doc,
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.msgprint({
                                title: __("Cleanup Successful"),
                                indicator: "green",
                                message: __("Logs cleared: {0}<br>Cache cleared: {1}<br>Git optimized: {2}",
                                    [r.message.logs, r.message.cache, r.message.git])
                            });
                            frm.reload_doc();
                        }
                    }
                });
            });
        }).addClass("btn-primary");
    }
});
