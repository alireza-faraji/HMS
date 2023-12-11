frappe.listview_settings['Inn Payment with Settlement'] = {
    onload: function (listview) {
        // listview.page.add_menu_item(__('Check In'), function() {
        //
        // });
        frappe.call({
            method: 'inn.hms_module.doctype.inn_payment_with_settlement.inn_payment_with_settlement.get_all_mode_of_payment_settlement',
            callback: (r) => {

            }
        });
    }
}