import frappe
from datetime import datetime


no_cache = 1
base_template_path = "www/security.txt"


def get_context(context):
    context.raw_file = frappe.get_value("Humans TXT", None, "raw_file")