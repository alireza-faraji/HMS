# Copyright (c) 2024, Core Initiative and contributors
# For license information, please see license.txt

# import frappe


from collections import OrderedDict

import frappe
from frappe import _, _dict
from frappe.utils import cstr, getdate

def execute(filters=None):
	if not filters:
		columns, data = [], []
	columns = get_columns(filters)
	data = get_result(filters)
	return columns, data

def get_result(filters):

	entries = get_entries(filters)

	data = get_total(filters,entries)

	result = get_result_as_list(data, filters)

	return result

def get_entries(filters):
	select_fields = """`tabHMS Folio Transaction`.owner,`tabHMS Folio Transaction`.audit_date,`tabHMS Folio Transaction`.modified_by,`tabHMS Folio Transaction`.transaction_type, `tabHMS Folio Transaction`.amount, `tabHMS Folio Transaction`.parent,`tabHMS Folio`.customer_id """
	#select_fields = """owner,audit_date"""

	# if filters.get("show_remarks"):
	# 	select_fields += """,remarks"""

	order_by_statement = "order by `tabHMS Folio Transaction`.owner,`tabHMS Folio Transaction`.audit_date"


		
	entries = frappe.db.sql(
		"""
		select
			{select_fields}
		from `tabHMS Folio Transaction` inner join `tabHMS Folio` on `tabHMS Folio Transaction`.parent=`tabHMS Folio`.name
		where {conditions}
		{order_by_statement}
	""".format(
			select_fields=select_fields,
			conditions=get_conditions(filters),
			order_by_statement=order_by_statement
		),
		filters,
		as_dict=1,
	)

	return entries


def get_total(filters,entries):
	return entries


def get_conditions(filters):
	conditions = []
	conditions.append("`tabHMS Folio Transaction`.transaction_type = 'Payment'")

	if filters.get("from_date"):
	 	conditions.append(" `tabHMS Folio Transaction`.audit_date >= %(from_date)s")

	if filters.get("to_date"):
	 	conditions.append(" `tabHMS Folio Transaction`.audit_date <= %(to_date)s")
	
	if filters.get("user"):
	 	conditions.append(" `tabHMS Folio Transaction`.owner = %(user)s")

	
	return "{}".format(" and ".join(conditions)) if conditions else "True"

def get_result_as_list(data, filters):
	 
	for d in data:
		print(d)
	return data

def get_columns(filters):
	columns = [
	
	{"label": _("Created By"), "fieldname": "owner", "fieldtype": "Data", "width": 250},
	{
		"label": _("Audit Date"),
		"fieldname": "audit_date",
		"fieldtype": "DateTime",
		"width": 140,
	},
	
	{"label": _("Amount"), "fieldname": "amount", "fieldtype": "Float", "width": 150},
	{"label": _("Folio"), "fieldname": "parent", "fieldtype": "Link","options":"HMS Folio", "width": 150},
	{"label": _("Customer"), "fieldname": "customer_id", "fieldtype": "Link","options":"Customer", "width": 200},
	]
	return columns
