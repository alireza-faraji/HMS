# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "hms"
app_title = "Hms Module"
app_publisher = "Core Initiative"
app_description = "Apps for handling hotel business"
app_icon = "octicon octicon-book"
app_color = "blue"
app_email = "info@coreinitiative.id"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/hms/css/hms.css"
# app_include_js = "/assets/hms/js/hms.js"

# include js, css files in header of web template
# web_include_css = "/assets/hms/css/hms.css"
# web_include_js = "/assets/hms/js/hms.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "hms.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "hms.install.before_install"
# after_install = "hms.config.setup.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "hms.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	# 	"*": {
	# 		"on_update": "method",
	# 		"on_cancel": "method",
	# 		"on_trash": "method"
	# }
	"HMS Tax": {
		"validate": "hms.hms_module.doctype.hms_tax.hms_tax.autofill_hms_tax_value"
	},
	"HMS Room Rate": {
		"validate": "hms.hms_module.doctype.hms_room_rate.hms_room_rate.calculate_total_amount"
	},
	"HMS Room": {
		"validate": "hms.hms_module.doctype.hms_room.hms_room.calculate_total_amenities_cost"
	},
	"HMS Folio Transaction": {
		"validate": "hms.hms_module.doctype.hms_folio_transaction.hms_folio_transaction.add_audit_date"
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
# 	"all": [
# 		"hms.tasks.all"
# 	],
# 	"daily": [
# 		"hms.tasks.daily"
# 	],
# 	"hourly": [
# 		"hms.tasks.hourly"
# 	],
	"weekly": [
		"hms.hms_module.doctype.hms_module_setting.hms_module_setting.generate_supervisor_passcode"
	]
# 	"monthly": [
# 		"hms.tasks.monthly"
# 	]
}

# Testing
# -------

# before_tests = "hms.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "hms.event.get_events"
# }

jenv = {
	"methods": [
		"get_total_deposit:hms.hms_module.doctype.hms_reservation.hms_reservation.get_total_deposit",
		"get_date:hms.hms_module.doctype.hms_reservation.hms_reservation.get_date"
	]
}