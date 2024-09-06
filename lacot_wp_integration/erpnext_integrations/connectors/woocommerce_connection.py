import json

import frappe
from frappe import _
from erpnext.erpnext_integrations.connectors.woocommerce_connection import (
	verify_request
)
from lacot_wp_integration.erpnext_integrations.connectors.order_processor import OrderProcessor

@frappe.whitelist(allow_guest=True)
def order(*args, **kwargs):
	try:
		return _order(*args, **kwargs)
	except Exception:
		error_message = (
			frappe.get_traceback() + "\n\n Request Data: \n" + json.loads(frappe.request.data).__str__()
		)
		frappe.log_error("WooCommerce Error", error_message)
		raise


def _order(*args, **kwargs):
	woocommerce_settings = frappe.get_doc("Woocommerce Settings")

	if frappe.flags.woocomm_test_order_data:
		order = frappe.flags.woocomm_test_order_data
		event = "created"

	elif frappe.request and frappe.request.data:
		verify_request()
		try:
			order = json.loads(frappe.request.data)
		except ValueError:
			# woocommerce returns 'webhook_id=value' for the first request which is not JSON
			order = frappe.request.data
		event = frappe.get_request_header("X-Wc-Webhook-Event")

	else:
		return "success"

	if event == "created" or event == "updated":
		# switch to Administrator to process the order
		frappe.set_user(woocommerce_settings.creation_user)
		return OrderProcessor(woocommerce_settings).process_event(order)