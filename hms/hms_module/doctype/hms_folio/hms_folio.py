
# -*- coding: utf-8 -*-
# Copyright (c) 2020, Core Initiative and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import math
import json
import datetime
from frappe.model.document import Document

class HMSFolio(Document):
	pass

@frappe.whitelist()
def create_folio(reservation_id):
	if not frappe.db.exists('HMS Folio', {'reservation_id': reservation_id}):
		reservation = frappe.get_doc('HMS Reservation', reservation_id)

		doc = frappe.new_doc('HMS Folio')
		doc.type = 'Guest'
		doc.reservation_id = reservation_id
		doc.customer_id = reservation.customer_id
		doc.open = reservation.expected_arrival
		doc.close = reservation.expected_departure
		doc.insert()

@frappe.whitelist()
def get_customer_and_folio_with_room_number(room_name):
	try:
		Reservation = frappe.get_last_doc('HMS Reservation', filters={"status": "In House","actual_room_id":room_name})
		folio=frappe.db.get_value('HMS Folio', {'reservation_id': Reservation.name})
		return{
			"status":"ok",
			"customer_name":Reservation.customer_id,
			"folio_name":folio
		}
	except Exception as e:
		return{
		"status":"error",
		}
	

def update_close_by_reservation(reservation_id):
	folio_list = frappe.get_all('HMS Folio', filters={'reservation_id': reservation_id})
	reservation = frappe.get_doc('HMS Reservation', reservation_id)
	# Update except status finish, because when Checking Out, Close is handled by close_folio function
	if reservation.status != 'Finish':
		for item in folio_list:
			doc_folio = frappe.get_doc('HMS Folio', item.name)
			# (frm.doc.actual_room_id === undefined || frm.doc.actual_room_id == null || frm.doc.actual_room_id === '')
			if reservation.departure==None:
				doc_folio.close = reservation.expected_departure.strftime('%Y-%m-%d')
			else:
				doc_folio.close = reservation.departure.strftime('%Y-%m-%d')
			doc_folio.save()

@frappe.whitelist()
def get_reservation_id(folio_id):
	doc = frappe.get_doc('HMS Folio', folio_id)
	return doc.reservation_id

@frappe.whitelist()
def update_balance(folio_id):
	doc = frappe.get_doc('HMS Folio', folio_id)
	trx_list = doc.get('folio_transaction')
	total_debit = 0.0
	total_credit = 0.0
	for trx in trx_list:
		if trx.flag == 'Debit' and trx.is_void == 0:
			total_debit += float(trx.amount)
		elif trx.flag == 'Credit' and trx.is_void == 0:
			total_credit += float(trx.amount)
	balance = total_credit - math.ceil(total_debit)

	if balance != doc.balance:
		frappe.db.set_value('HMS Folio', doc.name, 'total_debit', math.ceil(total_debit))
		frappe.db.set_value('HMS Folio', doc.name, 'total_credit', total_credit)
		frappe.db.set_value('HMS Folio', doc.name, 'balance', int(balance))

	return total_debit, total_credit, balance

@frappe.whitelist()
def need_to_update_balance(folio_id):
	doc = frappe.get_doc('HMS Folio', folio_id)
	trx_list = doc.get('folio_transaction')

	total_debit = 0.0
	total_credit = 0.0
	for trx in trx_list:
		if trx.flag == 'Debit' and trx.is_void == 0:
			total_debit += float(trx.amount)
		elif trx.flag == 'Credit' and trx.is_void == 0:
			total_credit += float(trx.amount)
	balance = total_credit - total_debit

	if balance != doc.balance:
		return 1
	else:
		return 0


@frappe.whitelist()
def get_balance(folio_id):
	update_balance(folio_id)
	return frappe.db.get_value('HMS Folio', folio_id, ['balance'])

@frappe.whitelist()
def get_balance_by_reservation(reservation_id):
	folio = frappe.get_doc('HMS Folio', {'reservation_id': reservation_id})
	balance = get_balance(folio.name)
	return balance

@frappe.whitelist()
def transfer_to_another_folio(trx_list, old_parent, new_parent):
	exist_error = 0
	list_json = json.loads(trx_list)
	for trx in list_json:
		trx_doc = frappe.get_doc('HMS Folio Transaction', trx)
		if trx_doc.parent == old_parent:
			trx_doc.parent = new_parent
			trx_doc.remark = 'Transferred from ' + old_parent + ' to Folio ' + new_parent
			trx_doc.save()
		else:
			exist_error = 1

	return exist_error

def is_using_city_ledger(folio_id):
	is_using = False
	doc = frappe.get_doc('HMS Folio', folio_id)
	trx_list = doc.get('folio_transaction')
	for trx in trx_list:
		if trx.is_void == 0 and trx.flag == 'Credit' and trx.mode_of_payment == 'City Ledger':
			is_using = True
	return is_using

@frappe.whitelist()
def close_folio(folio_id):
	list = check_void_request(folio_id)
	if len(list) == 0:
		folio = frappe.get_doc('HMS Folio', folio_id)
		folio.status = 'Closed'
		folio.close = datetime.date.today()
		folio.save()

		# Create AR City Ledger if There are payment using City Ledger as mode_of_payment
		if is_using_city_ledger(folio_id):
			total_amount = 0.0
			trx_list = frappe.get_all('HMS Folio Transaction', filters={'parent': folio_id, 'is_void': 0, 'flag': 'Credit',
																		'mode_of_payment': 'City Ledger'}, fields=['amount'])
			for trx in trx_list:
				total_amount += trx.amount

			ar_city_ledger = frappe.new_doc('AR City Ledger')
			ar_city_ledger.naming_series = 'AR-CL-.YYYY.-'
			ar_city_ledger.is_paid = 0
			ar_city_ledger.customer_id = folio.customer_id
			if folio.type == 'Guest':
				ar_city_ledger.hms_channel_id = frappe.db.get_value('HMS Reservation', folio.reservation_id, 'channel')
			else:
				ar_city_ledger.hms_group_id = folio.group_id
			ar_city_ledger.total_amount = total_amount
			ar_city_ledger.folio_id = folio_id
			ar_city_ledger.folio_type = folio.type
			ar_city_ledger.folio_status = folio.status
			ar_city_ledger.folio_open = folio.open
			ar_city_ledger.folio_close = folio.close
			ar_city_ledger.insert()

		return frappe.db.get_value('HMS Folio', folio_id, 'status')
	else:
		return "There are void transaction request that still not responded. " \
			   "Please consult the supervisor to resolve this before closing Folio." + \
			   "<br /> Transaction need to be resolved: <br />" + list


@frappe.whitelist()
def check_void_request(folio_id):
	need_resolve = []
	folio = frappe.get_doc('HMS Folio', folio_id)
	trx_list = folio.get('folio_transaction')
	for item in trx_list:
		if item.is_void == 0 and item.void_id is not None:
			if frappe.db.get_value('HMS Void Folio Transaction', {'name': item.void_id }, 'status') == 'Requested':
				need_resolve.append(item.name)
	return need_resolve
