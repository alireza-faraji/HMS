frappe.listview_settings['HMS Reservation'] = {
    get_indicator: function(doc) {
        return [__(doc.status), {
            "Reserved": "orange",
            "In House": "green",
            "Finish": "blue",
            "Cancel": "red",
            "No Show": "black"
        }[doc.status], "status,=," + doc.status];
	},
    onload: function (listview) {
        listview.page.add_action_item(__('Check In'), function() {
            console.log(listview.get_checked_items(true).length);
            if (listview.get_checked_items(true).length === 1) {
                frappe.call({
                    method: "hms.hms_module.doctype.hms_reservation.hms_reservation.start_check_in",
                    args: {
                        source: 'list',
                        reservation: listview.get_checked_items(true)
                    },
                    callback: (r) => {
                        if (r.message) {
                            var w = window.open(r.message, "_blank");
                        }
                    }
                })
            }
            else {
                frappe.msgprint("Please only select one reservation at a time");
            }

        });
        listview.page.add_action_item(__('Cancel'), function () {
            let reservation_to_cancel = listview.get_checked_items(true);
            frappe.confirm(
                ('You are about to Cancel Reservations ' + reservation_to_cancel + '. Are you sure?'),
                () => {
                    frappe.call({
                        method: 'hms.hms_module.doctype.hms_reservation.hms_reservation.cancel_reservation',
                        args: {
                            source: 'list',
                            reservation: reservation_to_cancel
                        },
                        callback: (r) => {
                            if (r.message === 1) {
                                frappe.msgprint("For Bulk Cancellation in Reservation List Page, only Reservation with status Reserved can be cancelled.<br />" +
                                    " Please choose Reservation with Reserved Status only. For Cancelling In House Reservation, go to Reservation Page.");
                            }
                            else if (r.message === 0) {
                                cur_list.refresh();
                                frappe.msgprint("Reservations " + reservation_to_cancel + " successfully canceled.");
                            }
                        }
                    });
                }
            );
        });
        listview.page.add_action_item(__('No Show'), function () {
            let reservation_to_no_show = listview.get_checked_items(true);
            frappe.confirm(
                ('You are about set Reservation(s) ' + reservation_to_no_show + ' status to No Show. Are you sure?'),
                () => {
                    frappe.call({
                        method: 'hms.hms_module.doctype.hms_reservation.hms_reservation.no_show_reservation',
                        args: {
                            source: 'list',
                            reservation: reservation_to_no_show
                        },
                        callback: (r) => {
                            if (r.message === 1) {
                                frappe.msgprint("Only Reservation with status Reserved can be set to No Show. Please choose other Reservation");
                            }
                            else if (r.message === 0) {
                                cur_list.refresh();
                                frappe.msgprint("Reservations " + reservation_to_no_show + " successfully set to No Show.");
                            }
                        }
                    });
                }
            );
        });
    }
};