"""Thin client for Odoo's JSON-2 API (the replacement for deprecated XML-RPC).

Every call is: POST {ODOO_URL}/json/2/<model>/<method> with a JSON body of
the method's named arguments. Auth is an API key in a Bearer header, and
X-Odoo-Database picks the database.
"""

import logging
import os

import httpx
from dotenv import load_dotenv

load_dotenv()
for _name in ("httpx", "httpx2"):  # the HTTP library logs every request at INFO
    logging.getLogger(_name).setLevel(logging.WARNING)


class OdooError(RuntimeError):
    pass


def call(model: str, method: str, **kwargs):
    url = f"{os.environ['ODOO_URL']}/json/2/{model}/{method}"
    headers = {
        "Authorization": f"bearer {os.environ['ODOO_API_KEY']}",
        "X-Odoo-Database": os.environ["ODOO_DB"],
    }
    response = httpx.post(url, json=kwargs, headers=headers, timeout=30)
    if response.status_code >= 400:
        raise OdooError(f"{model}.{method} -> {response.status_code}: {response.text[:300]}")
    return response.json()


def search_read(model: str, domain: list, fields: list[str], limit: int = 50):
    return call(model, "search_read", domain=domain, fields=fields, limit=limit)


def create(model: str, values: dict) -> int:
    # create takes a list of dicts and returns a list of new ids
    return call(model, "create", vals_list=[values])[0]
