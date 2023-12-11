// Copyright (c) 2020, Core Initiative and contributors
// For license information, please see license.txt

frappe.ui.form.on('HMS Package', {
	refresh: function(frm) {

	},
	total_pax: function (frm) {
		calculate_amount_before_tax(frm);
	},
	hms_tax_id: function (frm) {
		calculate_amount_before_tax(frm);
	},
	total_amount_after_tax: function (frm) {
		calculate_amount_before_tax(frm);
	}
});

function calculate_amount_before_tax(frm) {
	if (frm.doc.total_amount_after_tax && frm.doc.hms_tax_id && frm.doc.total_pax) {
		frappe.call({
			method: 'inn.hms_module.doctype.hms_package.hms_package.calculate_amounts_before_tax',
			args: {
				amount_after_tax: frm.doc.total_amount_after_tax,
				tax_id: frm.doc.hms_tax_id,
				total_pax: frm.doc.total_pax
			},
			callback: (r) => {
				if (r.message) {
					console.log(r.message);
					frm.set_value('total_amount', r.message[0]);
					frm.set_value('amount_per_pax', r.message[1]);
				}
			}
		})
	}
}