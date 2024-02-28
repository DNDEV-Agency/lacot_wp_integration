import frappe
from frappe.model.db_query import DatabaseQuery
from frappe.utils import cint, flt

from functools import reduce
from woocommerce import API
from lacot_wp_integration.utils import make_batches 


# Get items stock data
def get_data(
	item_code=None, warehouse=None, item_group=None, sort_by="actual_qty", sort_order="desc"
):
	"""Return data to render the item dashboard"""
	filters = []
	if item_code:
		filters.append(["item_code", "=", item_code])
	if warehouse:
		filters.append(["warehouse", "=", warehouse])
	if item_group:
		lft, rgt = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"])
		items = frappe.db.sql_list(
			"""
			select i.name from `tabItem` i
			where exists(select name from `tabItem Group`
				where name=i.item_group and lft >=%s and rgt<=%s)
		""",
			(lft, rgt),
		)
		filters.append(["item_code", "in", items])
	try:
		# check if user has any restrictions based on user permissions on warehouse
		if DatabaseQuery("Warehouse", user=frappe.session.user).build_match_conditions():
			filters.append(["warehouse", "in", [w.name for w in frappe.get_list("Warehouse")]])
	except frappe.PermissionError:
		# user does not have access on warehouse
		return []

	items = frappe.db.get_all(
		"Bin",
		fields=[
			"item_code",
			"warehouse",
			"projected_qty",
			"reserved_qty",
			"reserved_qty_for_production",
			"reserved_qty_for_sub_contract",
			"actual_qty",
			"valuation_rate",
		],
		or_filters={
			"projected_qty": ["!=", 0],
			"reserved_qty": ["!=", 0],
			"reserved_qty_for_production": ["!=", 0],
			"reserved_qty_for_sub_contract": ["!=", 0],
			"actual_qty": ["!=", 0],
		},
		filters=filters,
		order_by=sort_by + " " + sort_order,
	)

	precision = cint(frappe.db.get_single_value("System Settings", "float_precision"))

	for item in items:
		item.update(
			{
				"item_name": frappe.get_cached_value("Item", item.item_code, "item_name"),
				"disable_quick_entry": frappe.get_cached_value("Item", item.item_code, "has_batch_no")
				or frappe.get_cached_value("Item", item.item_code, "has_serial_no"),
				"projected_qty": flt(item.projected_qty, precision),
				"reserved_qty": flt(item.reserved_qty, precision),
				"reserved_qty_for_production": flt(item.reserved_qty_for_production, precision),
				"reserved_qty_for_sub_contract": flt(item.reserved_qty_for_sub_contract, precision),
				"actual_qty": flt(item.actual_qty, precision),
			}
		)
	return items

def handle_stock_update(doc, trigger):
    if not frappe.get_single("Woocommerce Settings").enable_sync:
        print("////////////////////////////")
        print("sync not enabled")
        print("////////////////////////////")
        return
    
    '''
    Get items quantity data from below feild mapping
    Purchase Receipt => items (Purchase Receipt Item) => item_code
    Purchase Invoice => items (Purchase Invoice Item) => item_code 
    stock_entry => items (Stock Entry Detail) => item_code
    Pick List => locations (Pick List Item) => item_code
    Sales Invoice => items (Sales Invoice Item) => item_code
    Delivery Note => items (Delivery Note Item) => item_code
    '''
    mapping = {
        "Purchase Receipt": "items",
        "Purchase Invoice": "items",
        "Stock Entry": "items",
        "Pick List": "locations",
        "Sales Invoice": "items",
        "Delivery Note": "items"
    }

    item_codes = set()

    if doc.doctype in mapping:
        for item in doc.get(mapping[doc.doctype]):
            item_codes.add(item.item_code)
    
    print("////////////////////////////")
    print("syncing items", item_codes)
    print("////////////////////////////")
    frappe.enqueue(sync_items_stock_woocommerce, item_codes=list(item_codes), enqueue_after_commit=True)

def get_woocommerce_conn():
    woocommerce_settings = frappe.get_single("Woocommerce Settings")
    if not woocommerce_settings.woocommerce_server_url or not woocommerce_settings.api_consumer_key or not woocommerce_settings.api_consumer_secret:
        frappe.log_error(
            title="WooCommerce settings not configured",
            message="Please configure WooCommerce settings"
        )
        
    return API(
        url=woocommerce_settings.woocommerce_server_url,
        consumer_key=woocommerce_settings.api_consumer_key,
        consumer_secret=woocommerce_settings.api_consumer_secret,
        wp_api=True, # Enable the WP REST API integration
        version="wc/v3" # WooCommerce WP REST API version
    )

def get_items_ids_woocommerce(item_codes: list):
    wcapi = get_woocommerce_conn()
    products = wcapi.get("products", params={"sku": ",".join(item_codes)})
    if not products.ok:
        print(products.content)
        frappe.log_error(
            title="Failed to fetch products from WooCommerce",
            message=products.content
        )
        return {}
    products = products.json()
    return {product.get("sku"): product.get("id") for product in products}

def batch_update_woocommerce(item_codes: list, item_qty_map: dict):
    wcapi = get_woocommerce_conn()
    item_ids = get_items_ids_woocommerce(item_codes)
    payload = {
        "update": [{"id": item_ids.get(item_code), "stock_quantity": item_qty_map.get(item_code)} for item_code in item_codes],
    }
    res = wcapi.post("products/batch", payload)
    if not res.ok:
        frappe.log_error(
            title=f"Failed to update stock for products {', '.join(item_codes)}",
            message=res.content
        )

def get_items_qty(item_codes: list, warehouse: str):
    item_code_qty = {}
    if len(item_codes):
        for item_code in item_codes:
            stock = get_data(item_code=item_code, warehouse=warehouse)
            qty = reduce(lambda x, y: x + y, [item.get("actual_qty") for item in stock])
            item_code_qty[item_code] = qty
    else:
        stock = get_data(warehouse=warehouse)
        for item in stock:
            item_code = item.get("item_code")
            actual_qty = item.get("actual_qty")
            if actual_qty > 0:
                if item_code in item_code_qty:
                    item_code_qty[item_code] += actual_qty
                else:
                    item_code_qty[item_code] = actual_qty
    return item_code_qty

def sync_items_stock_woocommerce(item_codes: list = []):
    warehouse = frappe.get_single("Woocommerce Settings").warehouse
    if len(item_codes):
        batches = make_batches(item_codes, 100)
        for batch in batches:
            item_code_qty = get_items_qty(batch, warehouse)
            batch_update_woocommerce(batch, item_code_qty)
    else:
        stock_data = get_data(warehouse=warehouse)
        batches = make_batches(stock_data, 100)
        for batch in batches:
            item_code_qty = {}
            for item in batch:
                item_code = item.get("item_code")
                actual_qty = item.get("actual_qty")
                if actual_qty > 0:
                    if item_code in item_code_qty:
                        item_code_qty[item_code] += actual_qty
                    else:
                        item_code_qty[item_code] = actual_qty
            batch_update_woocommerce(list(item_code_qty.keys()), item_code_qty)

@frappe.whitelist()
def sync_items_stock_woocommerce_background():
    return frappe.enqueue(sync_items_stock_woocommerce, enqueue_after_commit=True)

def sync_item_stock_woocommerce(item_code: str, qty: int):
    wcapi = get_woocommerce_conn()

    products = wcapi.get("products", params={"sku": item_code}).json()

    if not len(products):
        print(f"Product with SKU {item_code} not found in WooCommerce")
        return

    for product in products:
        res = wcapi.put(
            "products/{}".format(product.get("id")),
            {"stock_quantity": qty}
        )

        if not res.ok:
            frappe.log_error(
                title=f"Failed to update stock for product {product.get('id')}",
                message=res.content
            )

