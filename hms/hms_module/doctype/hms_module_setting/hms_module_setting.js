// Copyright (c) 2020, Core Initiative and contributors
// For license information, please see license.txt

frappe.ui.form.on('Hms Module Setting', {
	refresh: function(frm) {
		if (frappe.user.has_role('Hotel Manager') ||
			frappe.user.has_role('Hotel Reservation User') ||
			frappe.user.has_role('Administrator')) {
			frm.add_custom_button(__('Show Supervisor Passcode'), function () {
				frappe.call({
					method: 'hms.hms_module.doctype.hms_module_setting.hms_module_setting.show_supervisor_passcode',
				});
			});
		}
	},fix_db: function(frm) {
		frappe.call({
			method: 'hms.hms_module.doctype.hms_module_setting.hms_module_setting.fix_db',
		});
	},
	folio_transaction_type_generator: function(frm) {
		frappe.call({
			method: 'hms.hms_module.doctype.hms_module_setting.hms_module_setting.generate_folio_transaction_type',
		});
	},
	bed_type_generator: function (frm) {
		frappe.call({
			method: 'hms.hms_module.doctype.hms_module_setting.hms_module_setting.generate_bed_type',
		});
	},
	room_type_generator: function (frm) {
		frappe.call({
			method: 'hms.hms_module.doctype.hms_module_setting.hms_module_setting.generate_room_type',
		});
	},
	hms_module_account_generator: function (frm) {
		frappe.confirm(__("This may take a while. Please <b>don't refresh</b> or <b>change the page</b> before the Success or Error Message popped up. Click <b>Yes</b> to continue"), function() {
			frappe.call({
				method: 'hms.hms_module.doctype.hms_module_setting.hms_module_setting.generate_hotel_account',
			});
		});
	},
	test: function () {
		frappe.call({
			method: 'hms.hms_module.doctype.hms_module_setting.hms_module_setting.generate_supervisor_passcode'
		});
	}
});
