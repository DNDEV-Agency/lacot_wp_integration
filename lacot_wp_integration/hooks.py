from . import __version__ as app_version

app_name = "lacot_wp_integration"
app_title = "Lacot Wp Integration"
app_publisher = "M Umer Farooq"
app_description = "Syncs product stock between wp woocommerce and ERPNext"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "umer2001.uf@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/lacot_wp_integration/css/lacot_wp_integration.css"
# app_include_js = "/assets/lacot_wp_integration/js/lacot_wp_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/lacot_wp_integration/css/lacot_wp_integration.css"
# web_include_js = "/assets/lacot_wp_integration/js/lacot_wp_integration.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "lacot_wp_integration/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Woocommerce Settings" : "public/js/woocommerce_settings.js"
}
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

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "lacot_wp_integration.install.before_install"
# after_install = "lacot_wp_integration.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "lacot_wp_integration.uninstall.before_uninstall"
# after_uninstall = "lacot_wp_integration.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "lacot_wp_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Purchase Receipt": {
		"on_submit": "lacot_wp_integration.lacot_wp_integration.stocks_handler.handle_stock_update",
		"on_cancel": "lacot_wp_integration.lacot_wp_integration.stocks_handler.handle_stock_update"
	},
	"Purchase Invoice": {
		"on_submit": "lacot_wp_integration.lacot_wp_integration.stocks_handler.handle_stock_update",
		"on_cancel": "lacot_wp_integration.lacot_wp_integration.stocks_handler.handle_stock_update"
	},
	"Stock Entry": {
		"on_submit": "lacot_wp_integration.lacot_wp_integration.stocks_handler.handle_stock_update",
		"on_cancel": "lacot_wp_integration.lacot_wp_integration.stocks_handler.handle_stock_update"
	},
	"Pick List": {
		"on_submit": "lacot_wp_integration.lacot_wp_integration.stocks_handler.handle_stock_update",
		"on_cancel": "lacot_wp_integration.lacot_wp_integration.stocks_handler.handle_stock_update"
	},
	"Sales Invoice": {
		"on_submit": "lacot_wp_integration.lacot_wp_integration.stocks_handler.handle_stock_update",
		"on_cancel": "lacot_wp_integration.lacot_wp_integration.stocks_handler.handle_stock_update"
	},
	"Delivery Note": {
		"on_submit": "lacot_wp_integration.lacot_wp_integration.stocks_handler.handle_stock_update",
		"on_cancel": "lacot_wp_integration.lacot_wp_integration.stocks_handler.handle_stock_update"
	},
	"Stock Reconciliation": {
		"on_submit": "lacot_wp_integration.lacot_wp_integration.stocks_handler.handle_stock_update",
		"on_cancel": "lacot_wp_integration.lacot_wp_integration.stocks_handler.handle_stock_update"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"lacot_wp_integration.tasks.all"
#	],
#	"daily": [
#		"lacot_wp_integration.tasks.daily"
#	],
#	"hourly": [
#		"lacot_wp_integration.tasks.hourly"
#	],
#	"weekly": [
#		"lacot_wp_integration.tasks.weekly"
#	]
#	"monthly": [
#		"lacot_wp_integration.tasks.monthly"
#	]
# }

# Testing
# -------

# before_tests = "lacot_wp_integration.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"erpnext.erpnext_integrations.connectors.woocommerce_connection.order": "lacot_wp_integration.erpnext_integrations.connectors.woocommerce_connection.order"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "lacot_wp_integration.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Request Events
# ----------------
# before_request = ["lacot_wp_integration.utils.before_request"]
# after_request = ["lacot_wp_integration.utils.after_request"]

# Job Events
# ----------
# before_job = ["lacot_wp_integration.utils.before_job"]
# after_job = ["lacot_wp_integration.utils.after_job"]

# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"lacot_wp_integration.auth.validate"
# ]

