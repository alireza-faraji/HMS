# -*- coding: utf-8 -*-
# Copyright (c) 2021, Core Initiative and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import random
import string
import frappe
import datetime
from dateutil.relativedelta import relativedelta
from frappe.model.document import Document

class hmsMembershipCard(Document):
	pass

def generate_card_number():
	digits = string.digits
	unique_number = ''.join(random.choice(digits) for i in range(6))
	current_year = datetime.datetime.now().year
	card_number = str(current_year) + str(unique_number)
	return  card_number

def is_exist_card_number(card_number):
	cards = frappe.get_all('HMS Membership Card', fields=['card_number'])
	if card_number in cards:
		return True
	else:
		return False

@frappe.whitelist()
def get_new_card_data():
	years_to_expire = frappe.db.get_single_value('Hms Module Setting', 'years_to_expire')
	# Generate new unique card_number
	while True:
		new_card = generate_card_number()
		if not is_exist_card_number(new_card):
			break
	# Generate expiry date
	expiry = datetime.date.today() + relativedelta(years=int(years_to_expire))
	location_created = frappe.get_doc('Global Defaults').default_company
	return new_card, expiry, location_created

@frappe.whitelist()
def generate_bulk_cards(amount, card_type):
	list = []
	for x in range(0, int(amount)):
		new_doc = frappe.new_doc('HMS Membership Card')
		new_card, expiry, location_created = get_new_card_data()
		new_doc.card_number = new_card
		new_doc.expiry_date = expiry
		new_doc.type = card_type
		new_doc.location_created = location_created
		new_doc.insert()
		list.append(new_doc.name)
	return list

@frappe.whitelist()
def check_card(query):
	if frappe.db.exists('HMS Membership Card', {'card_number': query}):
		card = frappe.get_doc('HMS Membership Card', {'card_number': query})
		return 'Membership found with type ' + card.type + ' and expiry date of ' + card.expiry_date.strftime('%d-%m-%Y')
	else:
		return 'Card with number ' + query + ' not found in System.'


@frappe.whitelist()
def get_years_to_expire():
	return frappe.db.get_single_value('Hms Module Setting', 'years_to_expire')