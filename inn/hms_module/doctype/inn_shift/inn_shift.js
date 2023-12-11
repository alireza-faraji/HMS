// Copyright (c) 2020, Core Initiative and contributors
// For license information, please see license.txt
var total_cash_count = 0;
var total_cash_qty = 0;
var total_payment = 0;
var total_cash_payment = 0;
var total_refund = 0;

frappe.ui.form.on('Inn Shift', {
	refresh: function(frm) {
		frm.set_df_property('sb5', 'hidden', 1);
	},
	onload: function(frm) {
		frm.set_df_property('total_cash_qty', 'hidden', 0);
		frm.get_field('cc_detail').grid.cannot_add_rows = true;
		frm.get_field('payment_detail').grid.cannot_add_rows = true;
		frm.get_field('refund_detail').grid.cannot_add_rows = true;
		if (frm.doc.__islocal === 1) {
			frm.set_df_property('sb4', 'hidden', 1);
			frappe.call({
				method: 'inn.hms_module.doctype.inn_shift.inn_shift.is_there_open_shift',
				callback: (r) => {
					if (r.message === 1) {
						frappe.set_route('List', 'Inn Shift');
						frappe.msgprint('A Shift already Opened. Please close it first before creating new one.');
					}
					else{
						let cash_count = [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000];
						frm.set_value('cc_detail', []);
						for (var i = 0; i < cash_count.length; i++) {
							var item = frm.add_child('cc_detail');
							item.nominal = cash_count[i];
							item.qty = 0;
							item.amount = 0;
						}
						frm.refresh_field('cc_detail');

						populate_payment_refund(frm, null);
					}
				}
			});
		}
		else {
			if (frm.doc.status === 'Open') {
				frm.set_df_property('opening', 'read_only', 1);
				populate_payment_refund(frm, frm.doc.name);
			}
			else {
				set_all_read_only();
				frm.disable_save();
			}
		}
	},
	print_cash_remittance_button: function (frm, cdt, cdn) {
		if (frm.doc.__unsaved) {
			frappe.msgprint("Please save the document changes first, before printing report");
		}
		else {
			let w = window.open(frappe.urllib.get_full_url("/printview?"
				+"doctype="+encodeURIComponent("Inn Shift")
				+"&name="+encodeURIComponent(cdn)
				+"&format="+encodeURIComponent("Cash Remittance")
				+"&no_letterhead=0"
				));

			if (!w) {
				frappe.msgprint(__("Please enable pop-ups")); return;
			}
		}
	},
	print_cashier_report_button: function(frm, cdt, cdn) {
		if (frm.doc.__unsaved) {
			frappe.msgprint("Please save the document changes first, before printing report");
		}
		else {
			let w = window.open(frappe.urllib.get_full_url("/printview?"
				+"doctype="+encodeURIComponent("Inn Shift")
				+"&name="+encodeURIComponent(cdn)
				+"&format="+encodeURIComponent("Cashier Report")
				+"&no_letterhead=0"
				));

			if (!w) {
				frappe.msgprint(__("Please enable pop-ups")); return;
			}
		}
	},
	opening: function (frm) {
		frappe.call({
			method: "inn.hms_module.doctype.inn_shift.inn_shift.get_max_opening_cash",
			callback: (r) => {
				if (r.message) {
					// Max Opening Cash == 0 means no Max
					if (parseInt(r.message) == 0) {
						frm.set_value('total_cash_count', calculate_total_cash_count(frm));
					}
					// Opening is over the max opening allowed
					else if ( frm.doc.opening > parseFloat(r.message)) {
						frappe.msgprint("Maximum Opening Cash Allowed is below " + format_currency(r.message, 'IDR') );
						frm.set_value('opening', 0);
					}
				}
				else {
					frappe.msgprint("Error getting Max Opening Cash Value in Hms Module Setting. Please define it First.")
				}
			}
		});

	},
	reset_cash_count: function (frm) {
		let cash_count = [100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000];
		frm.set_value('cc_detail', []);
		for (var i = 0; i < cash_count.length; i++) {
			var item = frm.add_child('cc_detail');
			item.nominal = cash_count[i];
			item.qty = 0;
			item.amount = 0;
		}
		frm.set_value('total_cash_qty', 0);
		frm.set_value('total_cash_count', 0);
		frm.refresh_field('cc_detail');
	},
	close_shift_button: function (frm) {
		if (frm.is_dirty()) {
			frappe.msgprint("There are changes  not yet saved in this Shift. Please save the shift first.");
		}
		else {
			frappe.confirm(__("You are about to close the shift. Are you sure?"), function() {
				frappe.call({
					method: "inn.hms_module.doctype.inn_shift.inn_shift.close_shift",
					args: {
						shift_id: frm.doc.name,
					},
					callback: (r) => {
						if (r.message) {
							frappe.show_alert(__("Shift Closed."));
							frm.reload_doc();
						}
					}
				});
			});
		}
	}
});
frappe.ui.form.on('Inn CC Detail',{
	qty: function (frm, cdt, cdn) {
		let child = locals[cdt][cdn];
		child.amount = child.nominal*child.qty;
		frm.refresh_field('cc_detail');

		frm.set_value('total_cash_count', calculate_total_cash_count(frm));
		frm.set_value('total_cash_qty', calculate_total_cash_qty(frm));
	}
});

function set_all_read_only() {
	cur_frm.set_df_property('close_shift_button', 'hidden', 1);
	cur_frm.set_df_property('customer_id', 'read_only', 1);
	cur_frm.get_field("cc_detail").grid.only_sortable();
	cur_frm.get_field("payment_detail").grid.only_sortable();
	cur_frm.get_field("refund_detail").grid.only_sortable();
	frappe.meta.get_docfield('Inn CC Detail', 'qty', cur_frm.docname).read_only = true;
}

function populate_payment_refund(frm, shift_id) {
	frappe.call({
		method: 'inn.hms_module.doctype.inn_shift.inn_shift.populate_cr_payment',
		args: {
			shift_id: shift_id
		},
		callback: (r_payment) => {
			frappe.call({
				method: 'inn.hms_module.doctype.inn_shift.inn_shift.populate_cr_refund',
				args: {
					shift_id: shift_id
				},
				callback: (r_refund) => {
					// Set payments
					if (r_payment.message[0]) {
						frm.set_value('cr_payment_transaction', []);
						$.each(r_payment.message[0], function (i, d) {
							let item = frm.add_child('cr_payment_transaction');
							item.type = d.type;
							item.trx_id = d.trx_id;
							item.reservation_id = d.reservation_id;
							item.folio_id = d.folio_id;
							item.customer_id = d.customer_id;
							item.account = d.account;
							item.amount = d.amount;
							item.user = d.user;
						});
						frm.refresh_field('cr_payment_transaction');
					}
					if (r_payment.message[1]) {
						frm.set_value('payment_detail', []);
						total_payment = 0;
						$.each(r_payment.message[1], function (i, d) {
							let item = frm.add_child('payment_detail');
							item.mode_of_payment = d.mode_of_payment;
							item.amount = d.amount;
							total_payment += d.amount;
							if (d.mode_of_payment === 'Cash') {
								total_cash_payment += d.amount;
							}
						});
						frm.set_value('total_payment', total_payment);
						console.log(r_payment.message);
						frm.refresh_field('payment_detail');
					}

					// Set Refunds
					if (r_refund.message[0]) {
						frm.set_value('cr_refund_transaction', []);
						$.each(r_refund.message[0], function (i, d) {
							let item = frm.add_child('cr_refund_transaction');
							item.type = d.type;
							item.trx_id = d.trx_id;
							item.reservation_id = d.reservation_id;
							item.folio_id = d.folio_id;
							item.customer_id = d.customer_id;
							item.account = d.account;
							item.amount = d.amount;
							item.user = d.user;
						});
						frm.refresh_field('cr_refund_transaction');
					}
					if (r_refund.message[1]) {
						frm.set_value('refund_detail', []);
						total_refund = 0;
						$.each(r_refund.message[1], function (i, d) {
							let item = frm.add_child('refund_detail');
							item.type = d.type;
							item.amount = d.amount;
							total_refund += d.amount;
						});
						frm.set_value('total_refund', total_refund);
						console.log(r_refund.message);
						frm.refresh_field('refund_detail');
					}
					frm.set_value('balance', frm.doc.opening + total_payment - total_refund);
					frm.set_value('cash_balance', frm.doc.opening + total_cash_payment - total_refund);
				}
			});
		}
	});
}

function calculate_total_cash_count(frm) {
	let cc_detail_list = frm.doc.cc_detail;
	total_cash_count = 0;
	for (var i = 0; i < cc_detail_list.length; i++) {
		total_cash_count += cc_detail_list[i].amount;
	}
	return total_cash_count;
}

function calculate_total_cash_qty(frm) {
	let cc_detail_list = frm.doc.cc_detail;
	total_cash_qty = 0;
	for (var i = 0; i < cc_detail_list.length; i++) {
		total_cash_qty += parseInt(cc_detail_list[i].qty, 10);
	}
	return total_cash_qty;
}