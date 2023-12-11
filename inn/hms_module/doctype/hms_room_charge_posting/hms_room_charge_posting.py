# -*- coding: utf-8 -*-
# Copyright (c) 2020, Core Initiative and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import json
import frappe
import math
import datetime
from frappe.model.document import Document
from inn.hms_module.doctype.hms_folio_transaction_type.hms_folio_transaction_type import get_accounts_from_id
from inn.hms_module.doctype.hms_folio_transaction.hms_folio_transaction import get_idx
from inn.hms_module.doctype.hms_audit_log.hms_audit_log import get_last_audit_date
from inn.hms_module.doctype.hms_tax.hms_tax import calculate_hms_tax_and_charges

class InnRoomChargePosting(Document):
	pass

@frappe.whitelist()
def is_there_open_room_charge_posting():
	if frappe.get_all('HMS Room Charge Posting', {'status': 'Open'}):
		return 1
	else:
		return 2

@frappe.whitelist()
def is_there_closed_room_charge_posting_at():
	date = get_last_audit_date().strftime('%Y-%m-%d')

	if frappe.db.exists('HMS Room Charge Posting', {'audit_date': date, 'status': 'Closed'}):
		return 1
	else:
		return 2

@frappe.whitelist()
def populate_tobe_posted():
	tobe_posted_list = []
	folio_list = frappe.get_all('HMS Folio', filters={'status': 'Open', 'type': 'Guest'}, fields=['*'])
	for item in folio_list:
		reservation = frappe.get_doc('HMS Reservation', item.reservation_id)
		if reservation.status == 'In House' or reservation.status == 'Finish':
			room_charge_remark = 'Room Charge: Room Rate (Nett): ' + reservation.actual_room_id + " - " + \
								 get_last_audit_date().strftime("%d-%m-%Y")
			if not frappe.db.exists('HMS Folio Transaction',
								{'parent': item.name, 'transaction_type': 'Room Charge', 'remark': room_charge_remark, 'is_void': 0}):
				tobe_posted = frappe.new_doc('HMS Room Charge To Be Posted')
				tobe_posted.reservation_id = item.reservation_id
				tobe_posted.folio_id = item.name
				tobe_posted.room_id = reservation.actual_room_id
				tobe_posted.customer_id = reservation.customer_id
				tobe_posted.room_rate_id = reservation.room_rate
				tobe_posted.actual_room_rate = reservation.actual_room_rate
				tobe_posted_list.append(tobe_posted)
	return tobe_posted_list

@frappe.whitelist()
def post_individual_room_charges(parent_id, tobe_posted_list):
	return_value = ''
	room_charge_posting_doc = frappe.get_doc('HMS Room Charge Posting', parent_id)
	list_json = json.loads(tobe_posted_list)
	# for difference calculations
	fdc_reservation = ''
	fdc_folio_trx_tax_name = ''
	for item in list_json:
		# Create HMS Folio Transaction Bundle
		ftb_doc = frappe.new_doc('HMS Folio Transaction Bundle')
		ftb_doc.transaction_type = 'Room Charge'
		ftb_doc.insert()

		# Posting Room Charge
		item_doc = frappe.get_doc('HMS Room Charge To Be Posted', item)
		accumulated_amount = 0.00
		room_charge_debit_account, room_charge_credit_account = get_accounts_from_id('Room Charge')
		reservation = frappe.get_doc('HMS Reservation', item_doc.reservation_id)
		fdc_reservation = reservation
		room_charge_folio_trx = frappe.new_doc('HMS Folio Transaction')
		room_charge_folio_trx.flag = 'Debit'
		room_charge_folio_trx.is_void = 0
		room_charge_folio_trx.idx = get_idx(item_doc.folio_id)
		room_charge_folio_trx.transaction_type = 'Room Charge'
		room_charge_folio_trx.amount = float(int(reservation.nett_actual_room_rate))
		accumulated_amount += float(int(reservation.nett_actual_room_rate))
		room_charge_folio_trx.debit_account = room_charge_debit_account
		room_charge_folio_trx.credit_account = room_charge_credit_account
		room_charge_folio_trx.remark = 'Room Charge: Room Rate (Nett): ' + item_doc.room_id + " - " + get_last_audit_date().strftime("%d-%m-%Y")
		room_charge_folio_trx.parent = item_doc.folio_id
		room_charge_folio_trx.parenttype = 'HMS Folio'
		room_charge_folio_trx.parentfield = 'folio_transaction'
		room_charge_folio_trx.ftb_id = ftb_doc.name
		room_charge_folio_trx.insert()

		return_value = return_value + '<li>' + room_charge_folio_trx.remark + '</li>'

		# Create HMS Folio Transaction Bundle Detail Item Room Charge
		ftbd_doc = frappe.new_doc('HMS Folio Transaction Bundle Detail')
		ftbd_doc.transaction_type = room_charge_folio_trx.transaction_type
		ftbd_doc.transaction_id = room_charge_folio_trx.name
		ftb_doc.append('transaction_detail', ftbd_doc)

		fdc_room_rate = frappe.get_doc('HMS Room Rate', fdc_reservation.room_rate)
		fdc_room_rate_tax = frappe.get_doc('HMS Tax', fdc_room_rate.room_rate_tax)
		fdc_room_rate_tax_breakdown = fdc_room_rate_tax.hms_tax_breakdown
		if fdc_room_rate_tax_breakdown[-1].breakdown_rate != 0.0:
			fdc_room_rate_tax_account = fdc_room_rate_tax_breakdown[-1].breakdown_account
		else:
			fdc_room_rate_tax_account = fdc_room_rate_tax_breakdown[-2].breakdown_account
		# Posting Room Charge Tax/Service
		room_tb_id, room_tb_amount, _ = calculate_hms_tax_and_charges(reservation.nett_actual_room_rate,
																	  reservation.actual_room_rate_tax)
		for index, room_tax_item_name in enumerate(room_tb_id):
			room_tax_doc = frappe.new_doc('HMS Folio Transaction')
			room_tax_doc.flag = 'Debit'
			room_tax_doc.is_void = 0
			room_tax_doc.idx = get_idx(item_doc.folio_id)
			room_tax_doc.transaction_type = 'Room Charge Tax/Service'
			room_tax_doc.amount = room_tb_amount[index]
			accumulated_amount += room_tb_amount[index]
			room_tax_doc.credit_account = frappe.get_doc('HMS Tax Breakdown', room_tax_item_name).breakdown_account
			room_tax_doc.debit_account = room_charge_debit_account
			room_tax_doc.remark = 'Room Charge Tax Room Rate ' + room_tax_item_name + ' : ' + item_doc.room_id + " - " + get_last_audit_date().strftime("%d-%m-%Y")
			room_tax_doc.parent = item_doc.folio_id
			room_tax_doc.parenttype = 'HMS Folio'
			room_tax_doc.parentfield = 'folio_transaction'
			room_tax_doc.ftb_id = ftb_doc.name
			room_tax_doc.insert()

			if room_tax_doc.credit_account == fdc_room_rate_tax_account:
				fdc_folio_trx_tax_name = room_tax_doc.name

			# Create HMS Folio Transaction Bundle Detail Item Room Charge Tax/Service
			ftbd_doc = frappe.new_doc('HMS Folio Transaction Bundle Detail')
			ftbd_doc.transaction_type = room_tax_doc.transaction_type
			ftbd_doc.transaction_id = room_tax_doc.name
			ftb_doc.append('transaction_detail', ftbd_doc)

		# Posting Breakfast Charge
		breakfast_charge_debit_account, breakfast_charge_credit_account = get_accounts_from_id('Breakfast Charge')
		breakfast_charge_folio_trx = frappe.new_doc('HMS Folio Transaction')
		breakfast_charge_folio_trx.flag = 'Debit'
		breakfast_charge_folio_trx.is_void = 0
		breakfast_charge_folio_trx.idx = get_idx(item_doc.folio_id)
		breakfast_charge_folio_trx.transaction_type = 'Breakfast Charge'
		breakfast_charge_folio_trx.amount = float(int(reservation.nett_actual_breakfast_rate))
		accumulated_amount += float(int(reservation.nett_actual_breakfast_rate))
		breakfast_charge_folio_trx.debit_account = breakfast_charge_debit_account
		breakfast_charge_folio_trx.credit_account = breakfast_charge_credit_account
		breakfast_charge_folio_trx.remark = 'Room Charge: Breakfast (Nett): ' + item_doc.room_id + " - " + get_last_audit_date().strftime("%d-%m-%Y")
		breakfast_charge_folio_trx.parent = item_doc.folio_id
		breakfast_charge_folio_trx.parenttype = 'HMS Folio'
		breakfast_charge_folio_trx.parentfield = 'folio_transaction'
		breakfast_charge_folio_trx.ftb_id = ftb_doc.name
		breakfast_charge_folio_trx.insert()

		# Create HMS Folio Transaction Bundle Detail Item Breakfast Charge
		ftbd_doc = frappe.new_doc('HMS Folio Transaction Bundle Detail')
		ftbd_doc.transaction_type = breakfast_charge_folio_trx.transaction_type
		ftbd_doc.transaction_id = breakfast_charge_folio_trx.name
		ftb_doc.append('transaction_detail', ftbd_doc)

		# Posting Breakfast Tax/Service
		breakfast_tb_id, breakfast_tb_amount, _ = calculate_hms_tax_and_charges(reservation.nett_actual_breakfast_rate,
																				reservation.actual_breakfast_rate_tax)
		for index, breakfast_tax_item_name in enumerate(breakfast_tb_id):
			breakfast_tax_doc = frappe.new_doc('HMS Folio Transaction')
			breakfast_tax_doc.flag = 'Debit'
			breakfast_tax_doc.is_void = 0
			breakfast_tax_doc.idx = get_idx(item_doc.folio_id)
			breakfast_tax_doc.transaction_type = 'Breakfast Charge Tax/Service'
			breakfast_tax_doc.amount = breakfast_tb_amount[index]
			accumulated_amount += breakfast_tb_amount[index]
			breakfast_tax_doc.credit_account = frappe.get_doc('HMS Tax Breakdown',
															 breakfast_tax_item_name).breakdown_account
			breakfast_tax_doc.debit_account = breakfast_charge_debit_account
			breakfast_tax_doc.remark = 'Breakfast Charge Tax Room Rate ' + breakfast_tax_item_name + ' : ' + item_doc.room_id + " - " + get_last_audit_date().strftime("%d-%m-%Y")
			breakfast_tax_doc.parent = item_doc.folio_id
			breakfast_tax_doc.parenttype = 'HMS Folio'
			breakfast_tax_doc.parentfield = 'folio_transaction'
			breakfast_tax_doc.ftb_id = ftb_doc.name
			breakfast_tax_doc.insert()

			# Create HMS Folio Transaction Bundle Detail Item Breakfast Charge Tax/Service
			ftbd_doc = frappe.new_doc('HMS Folio Transaction Bundle Detail')
			ftbd_doc.transaction_type = breakfast_tax_doc.transaction_type
			ftbd_doc.transaction_id = breakfast_tax_doc.name
			ftb_doc.append('transaction_detail', ftbd_doc)

		print("accumulated amount = " + str(accumulated_amount))
		print("math_ceil(accumulated amount) = " + str(math.ceil(accumulated_amount)))
		print("actual room rate = " + str(reservation.actual_room_rate))
		print ("abs = " + str(abs(math.ceil(accumulated_amount) - int(reservation.actual_room_rate))))
		if abs(math.ceil(accumulated_amount) - int(reservation.actual_room_rate)) != 0:
			difference = math.ceil(accumulated_amount) - int(reservation.actual_room_rate)
			# hasil perhitungan lebih besar daripada room rate yang tersimpan di db
			if difference > 0:
				adjusted_room_charge_amount = room_charge_folio_trx.amount
				adjusted_breakfast_charge_amount = breakfast_charge_folio_trx.amount
				for i in range(0, abs(difference)):
					adjusted_room_charge_amount = adjusted_room_charge_amount - 1.0
			# hasil perhitungan lebih kecil daripada room rate yang tersimpan di db
			elif difference < 0:
				adjusted_room_charge_amount = room_charge_folio_trx.amount
				adjusted_breakfast_charge_amount = breakfast_charge_folio_trx.amount
				fdc_folio_trx_tax = frappe.get_doc('HMS Folio Transaction', fdc_folio_trx_tax_name)
				adjusted_room_rate_tax_amount = fdc_folio_trx_tax.amount
				for i in range(0, abs(difference)):
					adjusted_room_rate_tax_amount = adjusted_room_rate_tax_amount + 1.0

			room_charge_folio_trx.amount = adjusted_room_charge_amount
			room_charge_folio_trx.save()
			breakfast_charge_folio_trx.amount = adjusted_breakfast_charge_amount
			breakfast_charge_folio_trx.save()
			fdc_folio_trx_tax.amount = adjusted_room_rate_tax_amount
			fdc_folio_trx_tax.save()

		# Resave Bundle to save Detail
		ftb_doc.save()

		posted = frappe.new_doc('HMS Room Charge Posted')
		posted.reservation_id = item_doc.reservation_id
		posted.folio_id = item_doc.folio_id
		posted.room_id = item_doc.room_id
		posted.customer_id = item_doc.customer_id
		posted.room_rate_id = item_doc.room_rate_id
		posted.actual_room_rate = item_doc.actual_room_rate
		posted.folio_transaction_id = room_charge_folio_trx.name
		posted.parent = parent_id
		posted.parentfield = 'already_posted'
		posted.parenttype = 'HMS Room Charge Posting'
		room_charge_posting_doc.append('already_posted', posted)

		frappe.delete_doc('HMS Room Charge To Be Posted', item_doc.name)

	room_charge_posting_doc.save()
	calculate_already_posted_total(room_charge_posting_doc.name)
	return return_value

@frappe.whitelist()
def post_room_charges(parent_id, tobe_posted_list):
	return_value = ''
	room_charge_posting_doc = frappe.get_doc('HMS Room Charge Posting', parent_id)
	list_json = json.loads(tobe_posted_list)
	# for difference calculations
	fdc_reservation = ''
	fdc_folio_trx_tax_name = ''
	for item in list_json:
		# Create HMS Folio Transaction Bundle
		ftb_doc = frappe.new_doc('HMS Folio Transaction Bundle')
		ftb_doc.transaction_type = 'Room Charge'
		ftb_doc.insert()

		# Posting Room Charge
		accumulated_amount = 0.00
		room_charge_debit_account, room_charge_credit_account = get_accounts_from_id('Room Charge')
		reservation = frappe.get_doc('HMS Reservation', item['reservation_id'])
		fdc_reservation = reservation
		room_charge_folio_trx = frappe.new_doc('HMS Folio Transaction')
		room_charge_folio_trx.flag = 'Debit'
		room_charge_folio_trx.is_void = 0
		room_charge_folio_trx.idx = get_idx(item['folio_id'])
		room_charge_folio_trx.transaction_type = 'Room Charge'
		room_charge_folio_trx.amount = float(int(reservation.nett_actual_room_rate))
		accumulated_amount += float(int(reservation.nett_actual_room_rate))
		room_charge_folio_trx.debit_account = room_charge_debit_account
		room_charge_folio_trx.credit_account = room_charge_credit_account
		room_charge_folio_trx.remark = 'Room Charge: Room Rate (Nett): ' + item[
			'room_id'] + " - " + get_last_audit_date().strftime("%d-%m-%Y")
		room_charge_folio_trx.parent = item['folio_id']
		room_charge_folio_trx.parenttype = 'HMS Folio'
		room_charge_folio_trx.parentfield = 'folio_transaction'
		room_charge_folio_trx.ftb_id = ftb_doc.name
		room_charge_folio_trx.insert()

		return_value = return_value + '<li>' + room_charge_folio_trx.remark + '</li>'

		# Create HMS Folio Transaction Bundle Detail Item Room Charge
		ftbd_doc = frappe.new_doc('HMS Folio Transaction Bundle Detail')
		ftbd_doc.transaction_type = room_charge_folio_trx.transaction_type
		ftbd_doc.transaction_id = room_charge_folio_trx.name
		ftb_doc.append('transaction_detail', ftbd_doc)

		fdc_room_rate = frappe.get_doc('HMS Room Rate', fdc_reservation.room_rate)
		fdc_room_rate_tax = frappe.get_doc('HMS Tax', fdc_room_rate.room_rate_tax)
		fdc_room_rate_tax_breakdown = fdc_room_rate_tax.hms_tax_breakdown
		if fdc_room_rate_tax_breakdown[-1].breakdown_rate != 0.0:
			fdc_room_rate_tax_account = fdc_room_rate_tax_breakdown[-1].breakdown_account
		else:
			fdc_room_rate_tax_account = fdc_room_rate_tax_breakdown[-2].breakdown_account
		# Posting Room Charge Tax/Service
		room_tb_id, room_tb_amount, _ = calculate_hms_tax_and_charges(reservation.nett_actual_room_rate,
																	  reservation.actual_room_rate_tax)
		for index, room_tax_item_name in enumerate(room_tb_id):
			room_tax_doc = frappe.new_doc('HMS Folio Transaction')
			room_tax_doc.flag = 'Debit'
			room_tax_doc.is_void = 0
			room_tax_doc.idx = get_idx(item['folio_id'])
			room_tax_doc.transaction_type = 'Room Charge Tax/Service'
			room_tax_doc.amount = room_tb_amount[index]
			accumulated_amount += room_tb_amount[index]
			room_tax_doc.credit_account = frappe.get_doc('HMS Tax Breakdown', room_tax_item_name).breakdown_account
			room_tax_doc.debit_account = room_charge_debit_account
			room_tax_doc.remark = 'Room Charge Tax Room Rate ' + room_tax_item_name + ' : ' + item[
				'room_id'] + " - " + get_last_audit_date().strftime("%d-%m-%Y")
			room_tax_doc.parent = item['folio_id']
			room_tax_doc.parenttype = 'HMS Folio'
			room_tax_doc.parentfield = 'folio_transaction'
			room_tax_doc.ftb_id = ftb_doc.name
			room_tax_doc.insert()

			if room_tax_doc.credit_account == fdc_room_rate_tax_account:
				fdc_folio_trx_tax_name = room_tax_doc.name

			# Create HMS Folio Transaction Bundle Detail Item Room Charge Tax/Service
			ftbd_doc = frappe.new_doc('HMS Folio Transaction Bundle Detail')
			ftbd_doc.transaction_type = room_tax_doc.transaction_type
			ftbd_doc.transaction_id = room_tax_doc.name
			ftb_doc.append('transaction_detail', ftbd_doc)

		# Posting Breakfast Charge
		breakfast_charge_debit_account, breakfast_charge_credit_account = get_accounts_from_id('Breakfast Charge')
		breakfast_charge_folio_trx = frappe.new_doc('HMS Folio Transaction')
		breakfast_charge_folio_trx.flag = 'Debit'
		breakfast_charge_folio_trx.is_void = 0
		breakfast_charge_folio_trx.idx = get_idx(item['folio_id'])
		breakfast_charge_folio_trx.transaction_type = 'Breakfast Charge'
		breakfast_charge_folio_trx.amount = float(int(reservation.nett_actual_breakfast_rate))
		accumulated_amount += float(int(reservation.nett_actual_breakfast_rate))
		breakfast_charge_folio_trx.debit_account = breakfast_charge_debit_account
		breakfast_charge_folio_trx.credit_account = breakfast_charge_credit_account
		breakfast_charge_folio_trx.remark = 'Room Charge: Breakfast (Nett): ' + item[
			'room_id'] + " - " + get_last_audit_date().strftime("%d-%m-%Y")
		breakfast_charge_folio_trx.parent = item['folio_id']
		breakfast_charge_folio_trx.parenttype = 'HMS Folio'
		breakfast_charge_folio_trx.parentfield = 'folio_transaction'
		breakfast_charge_folio_trx.ftb_id = ftb_doc.name
		breakfast_charge_folio_trx.insert()

		# Create HMS Folio Transaction Bundle Detail Item Breakfast Charge
		ftbd_doc = frappe.new_doc('HMS Folio Transaction Bundle Detail')
		ftbd_doc.transaction_type = breakfast_charge_folio_trx.transaction_type
		ftbd_doc.transaction_id = breakfast_charge_folio_trx.name
		ftb_doc.append('transaction_detail', ftbd_doc)

		# Posting Breakfast Tax/Service
		breakfast_tb_id, breakfast_tb_amount, _ = calculate_hms_tax_and_charges(reservation.nett_actual_breakfast_rate,
																				reservation.actual_breakfast_rate_tax)
		for index, breakfast_tax_item_name in enumerate(breakfast_tb_id):
			breakfast_tax_doc = frappe.new_doc('HMS Folio Transaction')
			breakfast_tax_doc.flag = 'Debit'
			breakfast_tax_doc.is_void = 0
			breakfast_tax_doc.idx = get_idx(item['folio_id'])
			breakfast_tax_doc.transaction_type = 'Breakfast Charge Tax/Service'
			breakfast_tax_doc.amount = breakfast_tb_amount[index]
			accumulated_amount += breakfast_tb_amount[index]
			breakfast_tax_doc.credit_account = frappe.get_doc('HMS Tax Breakdown',
															 breakfast_tax_item_name).breakdown_account
			breakfast_tax_doc.debit_account = breakfast_charge_debit_account
			breakfast_tax_doc.remark = 'Breakfast Charge Tax Room Rate ' + breakfast_tax_item_name + ' : ' + item[
				'room_id'] + " - " + get_last_audit_date().strftime("%d-%m-%Y")
			breakfast_tax_doc.parent = item['folio_id']
			breakfast_tax_doc.parenttype = 'HMS Folio'
			breakfast_tax_doc.parentfield = 'folio_transaction'
			breakfast_tax_doc.ftb_id = ftb_doc.name
			breakfast_tax_doc.insert()

			# Create HMS Folio Transaction Bundle Detail Item Breakfast Charge Tax/Service
			ftbd_doc = frappe.new_doc('HMS Folio Transaction Bundle Detail')
			ftbd_doc.transaction_type = breakfast_tax_doc.transaction_type
			ftbd_doc.transaction_id = breakfast_tax_doc.name
			ftb_doc.append('transaction_detail', ftbd_doc)

		print("accumulated amount = " + str(accumulated_amount))
		print("math_ceil(accumulated amount) = " + str(math.ceil(accumulated_amount)))
		print("actual room rate = " + str(reservation.actual_room_rate))
		print("abs = " + str(abs(math.ceil(accumulated_amount) - int(reservation.actual_room_rate))))
		if abs(math.ceil(accumulated_amount) - int(reservation.actual_room_rate)) != 0:
			difference = math.ceil(accumulated_amount) - int(reservation.actual_room_rate)
			if difference > 0:
				adjusted_room_charge_amount = room_charge_folio_trx.amount
				adjusted_breakfast_charge_amount = breakfast_charge_folio_trx.amount
				for i in range(0, abs(difference)):
					adjusted_room_charge_amount = adjusted_room_charge_amount - 1.0

			elif difference < 0:
				adjusted_room_charge_amount = room_charge_folio_trx.amount
				adjusted_breakfast_charge_amount = breakfast_charge_folio_trx.amount
				fdc_folio_trx_tax = frappe.get_doc('HMS Folio Transaction', fdc_folio_trx_tax_name)
				adjusted_room_rate_tax_amount = fdc_folio_trx_tax.amount
				# TODO: ganti tambah difference ke pajak, bukan ke room rate & breakfast
				for i in range(0, abs(difference)):
					adjusted_room_rate_tax_amount = adjusted_room_rate_tax_amount + 1.0

			room_charge_folio_trx.amount = adjusted_room_charge_amount
			room_charge_folio_trx.save()
			breakfast_charge_folio_trx.amount = adjusted_breakfast_charge_amount
			breakfast_charge_folio_trx.save()
			fdc_folio_trx_tax.amount = adjusted_room_rate_tax_amount
			fdc_folio_trx_tax.save()

		# Resave Bundle to save Detail
		ftb_doc.save()

		posted = frappe.new_doc('HMS Room Charge Posted')
		posted.reservation_id = item['reservation_id']
		posted.folio_id = item['folio_id']
		posted.room_id = item['room_id']
		posted.customer_id = item['customer_id']
		posted.room_rate_id = item['room_rate_id']
		posted.actual_room_rate = item['actual_room_rate']
		posted.folio_transaction_id = room_charge_folio_trx.name
		posted.parent = parent_id
		posted.parentfield = 'already_posted'
		posted.parenttype = 'HMS Room Charge Posting'
		room_charge_posting_doc.append('already_posted', posted)

		frappe.delete_doc('HMS Room Charge To Be Posted', item['name'])

	room_charge_posting_doc.save()
	calculate_already_posted_total(room_charge_posting_doc.name)

	return return_value

def calculate_already_posted_total(room_charge_posting_id):
	total = 0.0
	doc = frappe.get_doc('HMS Room Charge Posting', room_charge_posting_id)
	posted = doc.get('already_posted')
	if len(posted) > 0:
		for item in posted:
			total += item.actual_room_rate

	frappe.db.set_value('HMS Room Charge Posting', doc.name, 'already_posted_total', total)