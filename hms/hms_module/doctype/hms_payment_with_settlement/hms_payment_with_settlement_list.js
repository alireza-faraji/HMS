frappe.listview_settings['HMS Payment with Settlement'] = {
    onload: function (listview) {
        // listview.page.add_menu_item(__('Check In'), function() {
        //
        // });
        frappe.call({
            method: 'hms.hms_module.doctype.hms_payment_with_settlement.hms_payment_with_settlement.get_all_mode_of_payment_settlement',
            callback: (r) => {

            }
        });
    }
}