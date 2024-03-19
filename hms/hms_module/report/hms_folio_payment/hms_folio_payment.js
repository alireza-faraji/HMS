// Copyright (c) 2024, Core Initiative and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["HMS Folio Payment"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_days(frappe.datetime.get_today(), -1),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"user",
			"label": __("User"),
			"fieldtype": "Link",
			"default": "",
			"options":"User",
			"reqd": 0,
			"width": "60px"
		},
	]
};
