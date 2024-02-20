from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in lacot_wp_integration/__init__.py
from lacot_wp_integration import __version__ as version

setup(
	name="lacot_wp_integration",
	version=version,
	description="Syncs product stock between wp woocommerce and ERPNext",
	author="M Umer Farooq",
	author_email="umer2001.uf@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
