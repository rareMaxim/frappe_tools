import frappe
from datetime import datetime


no_cache = 1
base_template_path = "www/security.txt"


def get_context(context):
    meta = frappe.get_meta("security_txt")
    settings = frappe.get_single("security_txt")

    data = settings.as_dict(
        no_nulls=True, no_default_fields=True, convert_dates_to_str=False
    )
    context.secure_txt = []
    for k, v in data.items():
        if k in ["email", "phone", "contact_page"]:
            if k == "email":
                context.secure_txt.append({"Contact": "mailto:" + v})
            else:
                context.secure_txt.append({"Contact": v})
        elif k == "expires":
            context.secure_txt.append({k: datetime.strptime(v, "%Y-%m-%d %H:%M:%S").isoformat()})
        else:
            context.secure_txt.append({meta.get_field(k).label: v})
    # for field in meta.fields:
    #     settings.get
    # # Contact Info
    # if settings.email:
    #     context.data.append({"Contact": settings.email})
    # if settings.contact_page:
    #     context.data.append({"Contact": settings.contact_page})
    # if settings.phone:
    #     context.data.append({"Contact": settings.phone})
    # # Other Info
    # if settings.expires:
    #     context.data.append({"Contact": settings.expires})
