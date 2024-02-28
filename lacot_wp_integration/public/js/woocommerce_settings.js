// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Woocommerce Settings', {
    refresh(frm) {
        frm.trigger("add_button_sync_stock");
    },

    add_button_sync_stock(frm) {
        frm.add_custom_button(__('Sync Stock'), () => {
            frappe.call({
                type: "GET",
                method: "lacot_wp_integration.lacot_wp_integration.stocks_handler.sync_items_stock_woocommerce_background",
            }).done(() => {
                frappe.msgprint(__("Stock sync has been initiated"));
            }).fail(() => {
                frappe.msgprint(__("Could not sync stock"));
            });
        });
    },
});