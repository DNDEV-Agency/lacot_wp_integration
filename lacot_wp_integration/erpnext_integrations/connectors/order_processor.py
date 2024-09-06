import frappe
from frappe import _
from frappe.utils import cstr
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice, make_delivery_note
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry   
from ecommerce_integrations.woocommerce.woocommerce_connection import (
	link_items,
	create_contact,
	create_address,
	rename_address,
	add_tax_details,
)

class OrderProcessor:
    def __init__(self, woocommerce_settings):
        self.order_states = set()
        self.woocommerce_settings = woocommerce_settings

    def process_event(self, event_payload):
        self.order_id = event_payload.get("id")
        event = event_payload.get("status")
        
        # Define the sequence of steps
        steps = {
            "pending": self.create_sales_order,
            "created": self.create_sales_order,
            "processing": self.create_delivery_note
        }

        # Add the current event to the order's state
        self.order_states.add(event)

        # Ensure all previous steps are completed
        for step in steps:
            if not self.__is_step_completed(self.order_id, step):
                steps[step](event_payload)
                self.order_states.add(step)
            
            # Break the loop once the current event is processed
            if step == event:
                break
        
        return {
            "order_id": self.order_id,
            "order_states": self.order_states
        }

    def __is_step_completed(self, order_id, step):
        def is_sales_order_created(order_id):
            return frappe.get_value("Sales Order", {"woocommerce_id": order_id})
        def is_payment_entry_created(order_id):
            pass
        def is_delivery_note_created(order_id):
            so_name = frappe.get_value("Sales Order", {"woocommerce_id": order_id})
            return frappe.db.exists("Delivery Note Item", {"against_sales_order": so_name})
        
        # Check if the step is completed based on the order's state
        steps = {
            "pending": is_sales_order_created,
            "created": is_sales_order_created,
            "processing": is_delivery_note_created
        }
        
        return steps[step](order_id)

    def create_sales_order(self, event_payload):
        sys_lang = frappe.get_single("System Settings").language or "en"
        link_customer_and_address(event_payload)
        customer_name = get_customer_name(event_payload)
        link_items(event_payload.get("line_items"), self.woocommerce_settings, sys_lang)
        
        acceptable_status_list = ["partial-payment", "processing","completed"]
        if not (event_payload.get("transaction_id") or event_payload.get("status") in acceptable_status_list):
            return frappe.throw("Order not paid yet")

        self.__create_sales_order(event_payload, self.woocommerce_settings, customer_name, sys_lang)
        self.create_payment_entry(event_payload)

    def create_payment_entry(self, event_payload):
        so_exists = frappe.get_value("Sales Order", {"woocommerce_id": self.order_id})
        if so_exists:
            so = frappe.get_doc("Sales Order", {"woocommerce_id": self.order_id})
            customer_name = get_customer_name(event_payload)
            self.__create_payment_entry(event_payload, self.woocommerce_settings, customer_name, so)

    def create_delivery_note(self, event_payload):
        so_exists = frappe.get_value("Sales Order", {"woocommerce_id": self.order_id})
        if so_exists:
            so = frappe.get_doc("Sales Order", {"woocommerce_id": self.order_id})
            dn = make_delivery_note(so.name)
            dn.insert(ignore_permissions=True)
            dn.submit()
            
    def __create_sales_order(self, order, woocommerce_settings, customer_name, sys_lang):
        new_sales_order = frappe.new_doc("Sales Order")
        new_sales_order.customer = customer_name
        new_sales_order.po_no = new_sales_order.woocommerce_id = order.get("id")
        new_sales_order.naming_series = woocommerce_settings.sales_order_series or "SO-WOO-"
        new_sales_order.company = woocommerce_settings.company
        new_sales_order.transaction_date = order.get("date_created").split("T")[0]
        new_sales_order.delivery_date = frappe.utils.add_days(order.get("date_created").split("T")[0], woocommerce_settings.delivery_after_days or 7)

        set_items_in_sales_order(new_sales_order, woocommerce_settings, order, sys_lang)
        new_sales_order.flags.ignore_mandatory = True
        new_sales_order.insert()
        new_sales_order.submit()

        frappe.db.commit()
        return new_sales_order
    
    def __create_payment_entry(self, order, woocommerce_settings, customer_name, ref):
        new_payment_entry = get_payment_entry("Sales Order", ref.name)
        new_payment_entry.posting_date = order.get("date_created").split("T")[0]
        new_payment_entry.reference_date = order.get("date_created").split("T")[0]
        new_payment_entry.reference_no = order.get("transaction_id") if order.get("transaction_id") != "" else [meta_data.get("value") for meta_data in order.get("meta_data") if meta_data.get("key") == "PaymentId"][0]
        new_payment_entry.save()
        new_payment_entry.submit()
        frappe.db.commit()
        # new_payment_entry.payment_type = "Receive"
        # new_payment_entry.mode_of_payment = "Credit Card"
        # new_payment_entry.paid_to = frappe.db.get_value("Company", woocommerce_settings.company, "default_income_account")
        # new_payment_entry.paid_to = frappe.db.get_value("Company", woocommerce_settings.company, "default_bank_account")
        # new_payment_entry.cost_center = frappe.db.get_value("Company", woocommerce_settings.company, "cost_center")
        # payment_reference = {
        #     "allocated_amount": float(order.get("total")),
        #     "due_date": order.get("date_created").split("T")[0],
        #     "reference_doctype": "Sales Order",
        #     "reference_name": ref.name,
        # }
        # new_payment_entry.append("references", payment_reference)

def set_items_in_sales_order(new_sales_order, woocommerce_settings, order, sys_lang):
	company_abbr = frappe.db.get_value("Company", woocommerce_settings.company, "abbr")

	default_warehouse = _("Stores - {0}", sys_lang).format(company_abbr)
	if not frappe.db.exists("Warehouse", default_warehouse) and not woocommerce_settings.warehouse:
		frappe.throw(_("Please set Warehouse in Woocommerce Settings"))

	for item in order.get("line_items"):
		woocomm_item_id = item.get("product_id")
		found_item = frappe.get_doc("Item", {"woocommerce_id": cstr(woocomm_item_id)})

		ordered_items_tax = item.get("total_tax")

		new_sales_order.append(
			"items",
			{
				"item_code": found_item.name,
				"item_name": found_item.item_name,
				"description": found_item.item_name,
				"uom": woocommerce_settings.uom or _("Nos", sys_lang),
				"qty": calculate_quantity(item),
				"rate": int(item["price"]),
				"warehouse": woocommerce_settings.warehouse or default_warehouse,
			},
		)

		add_tax_details(
			new_sales_order, ordered_items_tax, "Ordered Item tax", woocommerce_settings.tax_account
		)

	# shipping_details = order.get("shipping_lines") # used for detailed order

	add_tax_details(
		new_sales_order, order.get("shipping_tax"), "Shipping Tax", woocommerce_settings.f_n_f_account
	)
	add_tax_details(
		new_sales_order,
		order.get("shipping_total"),
		"Shipping Total",
		woocommerce_settings.f_n_f_account,
	)

def get_customer_name(payload):
        customer_woo_com_id = payload.get("customer_id")
        customer_woo_com_email = payload.get("billing").get("email")
        if customer_woo_com_id:
            customer_exists = frappe.get_value("Customer", {"woocommerce_id": customer_woo_com_id})
            if customer_exists:
                return frappe.get_value("Customer", {"woocommerce_id": customer_woo_com_id}, "name")
        else:
            customer_exists = frappe.get_value("Customer", {"woocommerce_email": customer_woo_com_email})
            if customer_exists:
                return frappe.get_value("Customer", {"woocommerce_email": customer_woo_com_email}, "name")
        return None

def link_customer_and_address(payload):
    raw_billing_data = payload.get("billing")
    raw_shipping_data = payload.get("shipping")
    customer_name = raw_billing_data.get("first_name") + " " + raw_billing_data.get("last_name")
    customer_woo_com_id = payload.get("customer_id")
    customer_woo_com_email = raw_billing_data.get("email")

    if customer_woo_com_id:
        customer_exists = frappe.get_value("Customer", {"woocommerce_id": customer_woo_com_id})
        if customer_exists:
            customer = frappe.get_doc("Customer", {"woocommerce_id": customer_woo_com_id})
            old_name = customer.customer_name
    else:
        customer_exists = frappe.get_value("Customer", {"woocommerce_email": customer_woo_com_email})
        if customer_exists:
            customer = frappe.get_doc("Customer", {"woocommerce_email": customer_woo_com_email})
            old_name = customer.customer_name

    if not customer_exists:
        # Create Customer
        customer = frappe.new_doc("Customer")

    customer.customer_name = customer_name
    customer.woocommerce_email = customer_woo_com_email
    if customer_woo_com_id:
        customer.woocommerce_id = customer_woo_com_id
        customer.custom_qwave_id = customer_woo_com_id
    customer.flags.ignore_mandatory = True
    customer.save(ignore_permissions=True)

    if customer_exists:
        if old_name != customer_name:
            frappe.rename_doc("Customer", old_name, customer_name)
        for address_type in (
            "Billing",
            "Shipping",
        ):
            try:
                address = frappe.get_doc(
                    "Address", {"woocommerce_email": customer_woo_com_email, "address_type": address_type}
                )
                rename_address(address, customer)
            except (
                frappe.DoesNotExistError,
                frappe.DuplicateEntryError,
                frappe.ValidationError,
            ):
                pass
    else:
        create_address(raw_billing_data, customer, "Billing")
        create_address(raw_shipping_data, customer, "Shipping")
        create_contact(raw_billing_data, customer)

def calculate_quantity(item):
	product_data = item.get("product_data", {})
	is_booking = product_data.get("type", None) == "booking"
	if is_booking:
		single_booking_price = float(product_data.get("price", 0))
		total_price_dict = next((d for d in item.get("meta_data", []) if d.get("key") == "_deposit_full_amount"), None)
		if total_price_dict:
			total_price = float(total_price_dict.get("value", 0))
			return round(total_price / single_booking_price)
	return item.get("quantity")