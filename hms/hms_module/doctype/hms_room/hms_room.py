# -*- coding: utf-8 -*-
# Copyright (c) 2020, Core Initiative and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import json
import frappe
from frappe.model.document import Document


class HMSRoom(Document):
	pass


@frappe.whitelist()
def copy_amenities_template(amenities_type_id):
	amenities_list = frappe.get_all('HMS Amenities', filters={'parent': amenities_type_id}, fields=['*'])
	return amenities_list


def calculate_total_amenities_cost(doc, method):
	amenities_list = doc.get('amenities')
	total_cost = 0.0
	for item in amenities_list:
		item_price = frappe.db.get_value('Item Price',
										 {'item_code': item.item, 'item_name': item.item_name, 'buying': 1},
										 ['price_list_rate'])
		total_cost += float(item_price) * float(item.qty)

	doc.total_amenities_cost = total_cost


@frappe.whitelist()
def get_room_status(room_id):
	return frappe.db.get_value('HMS Room', {'name': room_id}, "room_status")


@frappe.whitelist()
def get_all_hms_room(room_type):
	if room_type=='':
		return frappe.db.get_all('HMS Room',
							 fields=['name', 'room_type', 'bed_type', 'allow_smoke', 'view', 'room_status'],
							 order_by='name asc')
	else:
		return frappe.db.get_all('HMS Room',filters={"room_type":room_type},
							 fields=['name', 'room_type', 'bed_type', 'allow_smoke', 'view', 'room_status'],
							 order_by='name asc')
@frappe.whitelist()
def update_room_status(rooms, mode):
	is_failed = []
	is_housekeeping_assistant = False
	is_housekeeping_supervisor = False
	is_administrator = False

	for role in frappe.get_roles(frappe.session.user):
		if role == 'Housekeeping Assistant':
			is_housekeeping_assistant = True
		elif role == 'Housekeeping Supervisor':
			is_housekeeping_supervisor = True
		elif role == 'Administrator':
			is_administrator = True

	if mode == 'clean':
		for room in  json.loads(rooms):
			door_status = frappe.db.get_value('HMS Room', room, 'door_status')
			room_status = frappe.db.get_value('HMS Room', room, 'room_status')

			if door_status == 'No Status' or door_status == 'Sleeping Out':
				if room_status == 'Vacant Dirty':
					frappe.db.set_value('HMS Room', room, 'room_status', 'Vacant Clean')
				elif room_status == 'Occupied Dirty':
					frappe.db.set_value('HMS Room', room, 'room_status', 'Occupied Clean')
				elif room_status == 'Vacant Clean' and (is_housekeeping_supervisor or is_housekeeping_assistant or is_administrator):
					frappe.db.set_value('HMS Room', room, 'room_status', 'Vacant Ready')
				else:
					is_failed.append(room)

		if len(is_failed) > 0:
			return 'Some Rooms status updated. Some room status cannot be updated: ' + str(is_failed)
		else:
			return ' All Room status updated successfully.'
	elif mode == 'dirty':
		for room in json.loads(rooms):
			room_status = frappe.db.get_value('HMS Room', room, 'room_status')

			if room_status == 'Vacant Clean' or room_status == 'Vacant Ready':
				frappe.db.set_value('HMS Room', room, 'room_status', 'Vacant Dirty')
			elif room_status == 'Occupied Clean':
				frappe.db.set_value('HMS Room', room, 'room_status', 'Occupied Dirty')
			else:
				is_failed.append(room)

		if len(is_failed) > 0:
			return 'Some Rooms status updated. Some room status cannot be updated: ' + str(is_failed)
		else:
			return ' All Room status updated successfully.'

@frappe.whitelist()
def update_single_room_status(room, mode):
	is_failed = False
	is_housekeeping = False
	is_housekeeping_assistant = False
	is_housekeeping_supervisor = False
	is_administrator = False

	is_housekeeping_assistant = False
	is_housekeeping_supervisor = False
	is_administrator = False

	for role in frappe.get_roles(frappe.session.user):
		if role == 'Housekeeping Assistant':
			is_housekeeping_assistant = True
		elif role == 'Housekeeping Supervisor':
			is_housekeeping_supervisor = True
		elif role == 'Administrator':
			is_administrator = True

	if mode == 'clean':
		door_status = frappe.db.get_value('HMS Room', room, 'door_status')
		room_status = frappe.db.get_value('HMS Room', room, 'room_status')
		if door_status == 'No Status' or door_status == 'Sleeping Out':
			if room_status == 'Vacant Dirty':
				frappe.db.set_value('HMS Room', room, 'room_status', 'Vacant Clean')
			elif room_status == 'Occupied Dirty':
				frappe.db.set_value('HMS Room', room, 'room_status', 'Occupied Clean')
			elif room_status == 'Vacant Clean':
				if not is_housekeeping and ( is_housekeeping_supervisor or is_housekeeping_assistant or is_administrator):
					frappe.db.set_value('HMS Room', room, 'room_status', 'Vacant Ready')
				else:
					pass
			else:
				is_failed = True

		if is_failed:
			return 'Room Status cannot be updated. Please try again.'
		else:
			return 'Room ' + room + ' Status updated successfully'

	elif mode == 'dirty':
		room_status = frappe.db.get_value('HMS Room', room, 'room_status')

		if room_status == 'Vacant Clean' or room_status == 'Vacant Ready':
			frappe.db.set_value('HMS Room', room, 'room_status', 'Vacant Dirty')
		elif room_status == 'Occupied Clean':
			frappe.db.set_value('HMS Room', room, 'room_status', 'Occupied Dirty')
		else:
			is_failed = True

		if is_failed:
			return 'Room Status cannot be updated. Please try again.'
		else:
			return 'Room ' + room + ' Status updated successfully'
