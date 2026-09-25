"""
Thin client for the external GoFix customer service (GoFixAPI).

The base URL can be overridden with the GOFIX_API_BASE_URL environment
variable. Every call is bounded by a short timeout so a slow or down
GoFix service never hangs the buyback API.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv

load_dotenv(override=True)

GOFIX_API_BASE_URL = (
    os.getenv("GOFIX_API_BASE_URL") or "https://dotsmart-002-site1.gtempurl.com"
).rstrip("/")

GOFIX_API_TIMEOUT = float(os.getenv("GOFIX_API_TIMEOUT") or 10)


class GoFixServiceError(Exception):
    """Raised when the GoFix service cannot be reached or answers unexpectedly."""


def _get(path, **params):
    url = f"{GOFIX_API_BASE_URL}{path}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})

    try:
        with urllib.request.urlopen(request, timeout=GOFIX_API_TIMEOUT) as response:
            status = response.status
            body = response.read().decode("utf-8", errors="replace").strip()
    except urllib.error.HTTPError as exc:
        raise GoFixServiceError(f"GoFix service returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GoFixServiceError("GoFix service unreachable") from exc

    if status == 204 or not body:
        return None

    try:
        return json.loads(body)
    except ValueError as exc:
        raise GoFixServiceError("GoFix service returned an unreadable response") from exc


def is_customer_exists(phone):
    """True / False from GET /IsCustomerExists?phone=..."""
    result = _get("/IsCustomerExists", phone=phone)
    return bool(result)


def view_customer_by_phone(phone):
    """
    Basic customer record from GET /ViewCustomerByPhoneNo?phoneNo=...
    Returns None when the service answers 204 (no such customer).
    """
    result = _get("/ViewCustomerByPhoneNo", phoneNo=phone)
    if not isinstance(result, dict):
        return None
    return {
        "customer_id": result.get("customerId"),
        "customer_name": (result.get("name") or "").strip() or None,
        "mobile_no": phone,
        "email_id": (result.get("emailAddress") or "").strip() or None,
        "alternate_phone_no": (result.get("alternatePhoneNo") or "").strip() or None,
    }


def lookup_customer(phone):
    """
    Combined GoFix check.

    Returns (exists, record, error_message):
      exists  - True when GoFix knows the number
      record  - dict from view_customer_by_phone, or None
      error   - None, or a short message when the service could not be used
    """
    try:
        record = view_customer_by_phone(phone)
        if record:
            return True, record, None
        # ViewCustomerByPhoneNo gave nothing; fall back to the boolean check
        exists = is_customer_exists(phone)
        return exists, None, None
    except GoFixServiceError as exc:
        return False, None, str(exc)
