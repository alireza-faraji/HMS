// Copyright (c) 2020, Core Initiative and contributors
// For license information, please see license.txt

frappe.ui.form.on('HMS Room', {
	refresh: function(frm, cdt, cdn) {
		if (frappe.user.has_role('Housekeeping') ||
            frappe.user.has_role('Housekeeping Assistant') ||
            frappe.user.has_role('Housekeeping Supervisor') ||
            frappe.user.has_role('Administrator')) {
			if (frm.doc.room_status == 'Occupied Dirty' ||
				frm.doc.room_status == 'Vacant Dirty' ||
				frm.doc.room_status == 'Vacant Clean') {
				frm.page.add_menu_item(__('Clean Room'), function () {
					frappe.confirm(
						__('You are about to update status of Room ' + frm.doc.name + ', are you sure?'),
						() => {
						frappe.call({
							method: 'hms.hms_module.doctype.hms_room.hms_room.update_single_room_status',
							args: {
								room: frm.doc.name,
								mode: 'clean'
							},
							callback: (r) => {
								if (r.message) {
									frm.reload_doc();
									frappe.msgprint(r.message);
								}
							}
						});
					});
				})
			}
			else if (frm.doc.room_status == 'Vacant Clean' ||
					 frm.doc.room_status == 'Vacant Ready' ||
					 frm.doc.room_status == 'Occupied Clean') {
				frm.page.add_menu_item(__('Dirty Room'), function () {
					frappe.confirm(
						__('You are about to update status of Room ' + frm.doc.name + ', are you sure?'),
						() => {
						frappe.call({
							method: 'hms.hms_module.doctype.hms_room.hms_room.update_single_room_status',
							args: {
								room: frm.doc.name,
								mode: 'dirty'
							},
							callback: (r) => {
								if (r.message) {
									frm.reload_doc();
									frappe.msgprint(r.message);
								}
							}
						});
					});
				})
			}
		}
		frm.add_custom_button(__('Clear Door Status'), function () {
			frappe.db.set_value(cdt, cdn, 'door_status', 'No Status');
			frappe.show_alert('Door Status Cleared');
		});
		frm.add_custom_button(__('Do Not Disturb'), function () {
			if (frm.doc.room_status === 'Occupied Clean' || frm.doc.room_status === 'Occupied Dirty') {
				frappe.db.set_value(cdt, cdn, 'door_status', 'Do Not Disturb');
				frappe.show_alert('Door Status set to Do Not Disturb');
			}
			else {
				frappe.show_alert('Door Status cannot be changed in Vacant Room');
			}
		});
		frm.add_custom_button(__('Double Lock'), function () {
			if (frm.doc.room_status === 'Occupied Clean' || frm.doc.room_status === 'Occupied Dirty') {
				frappe.db.set_value(cdt, cdn, 'door_status', 'Double Lock');
				frappe.show_alert('Door Status set to Double Lock');
			}
			else {
				frappe.show_alert('Door Status cannot be changed in Vacant Room');
			}
		});
		frm.add_custom_button(__('Sleep Out'), function () {
			if (frm.doc.room_status === 'Occupied Clean' || frm.doc.room_status === 'Occupied Dirty') {
				frappe.db.set_value(cdt, cdn, 'door_status', 'Sleeping Out');
				frappe.show_alert('Door Status set to Sleep Out');
			}
			else {
				frappe.show_alert('Door Status cannot be changed in Vacant Room');
			}
		});
	},
	amenities_template: function (frm) {
		if (frm.doc.amenities_template) {
			frappe.call({
			method: "hms.hms_module.doctype.hms_room.hms_room.copy_amenities_template",
			args: {
				amenities_type_id: frm.doc.amenities_template
			},
			callback: (response) => {
				if (response.message) {
					frm.set_value('amenities', []);
					$.each(response.message, function (i, d) {
						var item = frm.add_child('amenities');
						item.item = d.item;
						item.item_name = d.item_name;
						item.qty = d.qty;
					});
				}
				frm.refresh_field('amenities');
			}
		})
		}
	}
});
