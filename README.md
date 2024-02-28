## Lacot Wp Integration

Syncs product stock between wp woocommerce and ERPNext

#### Features

- Sync stock between wp woocommerce and ERPNext Wharehouse/whole ERPNext

#### Installation

```bash
bench get-app https://github.com/DNDEV-Agency/lacot_wp_integration.git
bench --site site1.local install-app lacot_wp_integration
```

#### Configuration

Configure the app from WooCommerce Settings in ERPNext.
After selecting the Wharehouse click the **Sync Stock** button to sync the stock (**Note**: if the number of products is large, the sync may take around 5 min).

#### License

MIT