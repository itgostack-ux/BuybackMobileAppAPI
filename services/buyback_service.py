from repositories.buyback_repository import BuybackRepository
from services import grade_pricing as gp

repo = BuybackRepository()


class PriceError(Exception):
    """The ERP would stop with an error here. The API answers 400 with the text."""


def _diagnostic_answer_values(result):
    values = [result]

    if result == "Yes":
        values.append("Pass")
    elif result == "No":
        values.append("Fail")
    elif result == "Pass":
        values.append("Yes")
    elif result == "Fail":
        values.append("No")

    return values


def _plain(value):
    """TestResult.YES -> 'Yes'; any other value is returned unchanged."""
    return getattr(value, "value", value)


# =========================================================
# PRICING INPUTS (warranty status, device age, dead phone)
# =========================================================
def _take_pricing_inputs(payload):
    """
    The app answers the "Warranty" category like any other question:
        {"question_id": "WARRANTY_STATUS", "answer_value": "Out of Warranty"}
        {"question_id": "DEVICE_AGE", "answer_value": "7-11 Months"}

    Those two are not ERP questions. They are taken out of the answer list
    here, so they are not priced and not saved as answers, and are kept as
    warranty_status / device_age_months. Fields sent directly in the request
    win over the answers.
    """
    answers = []
    found = {}

    for r in payload.get("responses", []):
        kind = gp.pricing_input_kind(r.get("question_id"))

        if kind:
            found[kind] = _plain(r.get("answer_value"))
        else:
            answers.append(r)

    if not found:
        return payload

    updated = {**payload, "responses": answers}

    if updated.get("warranty_status") in (None, "") and "warranty" in found:
        updated["warranty_status"] = found["warranty"]

    if updated.get("device_age_months") is None and "age" in found:
        updated["device_age_months"] = found["age"]

    return updated


def _band_inputs(payload, is_dead):
    """
    (in_warranty, age_months) from the request. Both are required, as in
    the ERP, except for a dead phone.
    """
    sent_warranty = payload.get("warranty_status")
    sent_age = payload.get("device_age_months")

    in_warranty = gp.parse_warranty(sent_warranty)
    age = gp.resolve_age_months(sent_age)

    problems = []

    if in_warranty is None:
        if sent_warranty in (None, ""):
            problems.append(
                f"warranty_status is required ('{gp.IN_WARRANTY_TEXT}' or '{gp.OUT_OF_WARRANTY_TEXT}')"
            )
        else:
            problems.append(
                f"warranty_status '{sent_warranty}' was not understood. "
                f"Send '{gp.IN_WARRANTY_TEXT}' or '{gp.OUT_OF_WARRANTY_TEXT}'"
            )

    if age is None:
        if sent_age in (None, ""):
            problems.append(
                "device_age_months is required (the age in months, or the device age answer)"
            )
        else:
            problems.append(
                f"device_age_months '{sent_age}' was not understood. "
                f"Send the age in months, for example 14, or the device age answer"
            )

    if problems and not is_dead:
        raise PriceError("; ".join(problems))

    return in_warranty, age


def _item_context(item_code, payload):
    """
    (brand, item_group, family) of the phone: from the ERP item when it is
    known, else from the request. The family is 'Apple' or 'Android'.
    """
    try:
        context = repo.get_item_pricing_context(item_code) or {}
    except Exception:
        context = {}

    brand = context.get("brand") or payload.get("brand")
    item_group = context.get("item_group") or payload.get("item_group")
    family = context.get("family") or gp.family_from_brand(brand)

    return brand, item_group, family


def _pricing_rules(warnings):
    """The ERP's active Buyback Pricing Rules. [] with a warning when they cannot be read."""
    try:
        return repo.get_pricing_rules()
    except Exception:
        warnings.append("Buyback Pricing Rules could not be read, so none were applied")
        return []


def _max_deduction_percent(warnings):
    """Buyback Settings -> max_total_deduction_percent. None means the ERP default (100)."""
    try:
        return repo.get_buyback_setting("max_total_deduction_percent")
    except Exception:
        warnings.append("Buyback Settings could not be read, so the deduction limit 100% was used")
        return None


# =========================================================
# THE PRICE (shared by the three assessment APIs)
# =========================================================
def _price(payload, answers, diagnostics, warnings):
    """
    answers:     [{"question_id": ..., "answer_value": ...}]  ERP questions only
    diagnostics: [{"test_code": ..., "result": ...}]

    Returns (result, breakdown). Raises PriceError where the ERP would stop.
    """
    item_code = payload["item_code"]

    price_row = repo.get_price_row(item_code)
    if not price_row:
        raise PriceError("Price not found")

    is_dead = bool(payload.get("is_phone_dead"))
    in_warranty, age = _band_inputs(payload, is_dead)

    ids = [a.get("question_id") for a in answers] + [d.get("test_code") for d in diagnostics]
    options = repo.get_question_options(ids) if ids else {}

    items = [
        ("question", a.get("question_id"), _plain(a.get("answer_value")), options.get(a.get("question_id")))
        for a in answers
    ]

    for d in diagnostics:
        # a test result "No" also matches a "Fail" option, and "Yes" a "Pass" option
        values = _diagnostic_answer_values(_plain(d.get("result")))
        info = options.get(d.get("test_code"))
        chosen = next((value for value in values if gp.find_option(info, value)), values[0])
        items.append(("diagnostic", d.get("test_code"), chosen, info))

    brand, item_group, family = _item_context(item_code, payload)

    result = gp.calculate(
        price_row,
        in_warranty,
        age,
        items,
        family,
        _max_deduction_percent(warnings),
        is_dead,
        item_code,
        rules=[] if is_dead else _pricing_rules(warnings),
        brand=brand,
        item_group=item_group
    )

    if result.get("error"):
        raise PriceError(result["error"])

    breakdown = []
    counts = {}

    for line in result["lines"]:
        question_id = line["question_id"]
        counts[question_id] = counts.get(question_id, 0) + 1

        if not line["found"]:
            warnings.append(f"{question_id}: this question was not found, so it was counted as 0%")
        elif not line["matched"]:
            allowed = ", ".join(str(option.get("value")) for option in options[question_id]["options"])
            warnings.append(
                f"{question_id}: answer '{line['answer_value']}' is not one of [{allowed}], "
                f"so it was counted as 0%"
            )
        elif line.get("skipped") == "disabled":
            warnings.append(f"{question_id}: this question is disabled in the ERP, so it was counted as 0%")
        elif line.get("skipped") == "family":
            warnings.append(
                f"{question_id}: this question is for the other brand family, so it was counted as 0%"
            )

        breakdown.append({
            "type": line["type"],
            "question_id": question_id,
            "question_text": line["question_text"],
            "answer_value": line["answer_value"],
            "price_impact_percent": round(line["percent"], 2),
            "amount": round(line["amount"], 2),
            "matched": line["matched"],
            "counted": line["counted"],
            "fault_code": line["fault_code"]
        })

    for question_id, count in counts.items():
        if count > 1:
            warnings.append(
                f"{question_id} was answered {count} times; only its largest deduction was counted"
            )

    dropped_faults = sorted({
        line["fault_code"] for line in result["lines"]
        if line["fault_code"] and line["amount"] and not line["counted"]
        and counts.get(line["question_id"], 0) == 1
    })
    for fault_code in dropped_faults:
        warnings.append(
            f"Fault '{fault_code}' was reported by more than one answer; "
            f"only the largest deduction was counted"
        )

    return result, breakdown


def _save_grade_info(assessment_name, result, payload, warnings):
    """Writes grade, warranty and age on the assessment, in the ERP's own dropdown words."""
    try:
        selects = repo.get_doctype_select_options(
            "Buyback Assessment",
            ["estimated_grade", "warranty_status", "device_age_months"]
        )
    except Exception:
        selects = {}

    values = {
        "estimated_grade": gp.erp_grade_value(selects.get("estimated_grade"), result["grade"])
    }

    if result["in_warranty"] is not None:
        values["warranty_status"] = gp.erp_warranty_value(
            selects.get("warranty_status"), result["in_warranty"]
        )

    if result["age_months"] is not None:
        values["device_age_months"] = gp.erp_age_value(
            selects.get("device_age_months"), result["age_months"], payload.get("device_age_months")
        )

    try:
        repo.set_assessment_grade_info(assessment_name, values)
    except Exception:
        warnings.append(
            "The price was saved, but grade, warranty and age "
            "could not be saved on the assessment"
        )


def _reply(assessment_name, result, breakdown, warnings, with_diagnostics):
    base = result["base_price"]
    percent_of_base = (lambda amount: round(amount / base * 100, 2) if base else 0.0)

    question_total = sum(line["amount"] for line in result["lines"] if line["counted"] and line["type"] == "question")
    diagnostic_total = sum(line["amount"] for line in result["lines"] if line["counted"] and line["type"] == "diagnostic")

    reply = {
        "success": True,
        "assessment_name": assessment_name,
        "base_price": round(base, 2),
        "total_percent": percent_of_base(result["capped_total"]),
        "calculated_price": round(result["calculated_price"], 2),
        "floor_price": round(result["scrap_price"] or 0, 2),
        "estimated_price": round(result["final_price"], 2),
        "raw_percent": percent_of_base(result["raw_total"]),
        "response_percent": percent_of_base(question_total),
        "cap_applied": result["cap_applied"],
        "floor_applied": result["is_scrap"],
        "price_explanation": result["explanation"],
        "pricing_mode": result["mode"],
        "estimated_grade": result["grade"],
        "price_band": result["band"],
        "price_band_label": result["band_label"],
        "warranty_status": (
            None if result["in_warranty"] is None
            else (gp.IN_WARRANTY_TEXT if result["in_warranty"] else gp.OUT_OF_WARRANTY_TEXT)
        ),
        "device_age_months": result["age_months"],
        "grade_prices": result["grade_prices"],
        "total_deductions": round(result["capped_total"], 2),
        "rule_deductions": round(result.get("rule_total") or 0.0, 2),
        "max_deduction_percent": result["max_percent"],
        "is_scrap": result["is_scrap"],
        "is_phone_dead": result["is_phone_dead"],
        "breakdown": breakdown,
        "warnings": warnings
    }

    if with_diagnostics:
        reply["diagnostic_percent"] = percent_of_base(diagnostic_total)

    return reply


def _assess(payload, diagnostics, save):
    """Shared body of API 1 and API 2: price, save, reply."""
    payload = _take_pricing_inputs(payload)
    warnings = []

    try:
        result, breakdown = _price(payload, payload.get("responses", []), diagnostics or [], warnings)
    except PriceError as error:
        return {"success": False, "message": str(error)}

    name = save(payload, result["final_price"])
    _save_grade_info(name, result, payload, warnings)

    return _reply(name, result, breakdown, warnings, diagnostics is not None)


# =========================================================
# API 1: CREATE BASIC ASSESSMENT (RESPONSES ONLY)
# =========================================================
def create_buyback_service(payload: dict):
    return _assess(payload, None, repo.create_assessment)


# =========================================================
# API 2: CREATE FULL ASSESSMENT (RESP + DIAGNOSTICS)
# =========================================================
def create_full_buyback_service(payload: dict):
    return _assess(payload, payload.get("diagnostics", []), repo.create_full_assessment)


# =========================================================
# MOBILE: SubmitBuybackQuestionAnswers
# =========================================================
def submit_mobile_buyback_answers_service(payload: dict):
    customer = repo.get_customer_for_assessment(payload["customer_id"])
    if not customer:
        return {
            "success": False,
            "message": "Customer not found",
            "data": []
        }

    item = repo.get_item_for_assessment(payload["item_code"])
    if not item:
        return {
            "success": False,
            "message": "Item code not found in buyback price master",
            "data": []
        }

    saved_answers = []
    pricing_inputs = {}

    for index, answer in enumerate(payload.get("answers", []), start=1):
        question_name = answer.get("question_name")
        question_code = answer.get("question_code")

        if not question_name and not question_code:
            return {
                "success": False,
                "message": f"question_name or question_code is required in answer {index}",
                "data": []
            }

        # The "Warranty" category: these two answers choose the ERP price
        # band. They are not ERP questions, so they are not looked up or saved.
        kind = gp.pricing_input_kind(question_name) or gp.pricing_input_kind(question_code)
        if kind:
            pricing_inputs[kind] = answer.get("answer_value")
            continue

        question = repo.get_mapped_question_for_item(
            payload["item_code"],
            question_name=question_name,
            question_code=question_code
        )

        if not question:
            return {
                "success": False,
                "message": f"Question is not mapped for this item in answer {index}",
                "data": []
            }

        saved_answers.append({
            "question_name": question["name"],
            "question_code": question["question_code"],
            "question_text": question["question_text"],
            "answer_value": answer["answer_value"],
            "price_impact_percent": repo.get_price_percent(question["name"], answer["answer_value"])
        })

    pricing_payload = {
        "item_code": item["item_code"],
        "brand": item.get("brand"),
        "item_group": item.get("item_group"),
        "warranty_status": pricing_inputs.get("warranty"),
        "device_age_months": pricing_inputs.get("age"),
        "is_phone_dead": payload.get("is_phone_dead")
    }
    warnings = []

    try:
        result, breakdown = _price(
            pricing_payload,
            [{"question_id": a["question_name"], "answer_value": a["answer_value"]} for a in saved_answers],
            [],
            warnings
        )
    except PriceError as error:
        return {
            "success": False,
            "message": str(error),
            "data": []
        }

    assessment_name = repo.create_mobile_answer_assessment(
        payload,
        customer,
        item,
        saved_answers,
        result["final_price"]
    )

    _save_grade_info(assessment_name, result, pricing_payload, warnings)

    return {
        "success": True,
        "message": "Buyback answers submitted successfully",
        **_reply(assessment_name, result, breakdown, warnings, False),
        "customer_id": customer["name"],
        "item_code": item["item_code"],
        "answer_count": len(saved_answers),
        "final_price": round(result["final_price"], 2),
        "answers": saved_answers
    }


def create_sell_now_service(payload: dict):
    assessment = repo.get_assessment_for_sell_now(payload["assessment_name"])
    if not assessment:
        return {
            "success": False,
            "message": "Assessment not found",
            "data": []
        }

    existing_order = repo.get_order_by_assessment(payload["assessment_name"])
    if existing_order:
        return {
            "success": True,
            "message": "Sell now order already exists",
            "order_name": existing_order["name"],
            "assessment_name": existing_order["buyback_assessment"],
            "customer_id": existing_order["customer"],
            "item_code": existing_order["item"],
            "final_price": float(existing_order["final_price"] or 0),
            "approved_price": float(existing_order["approved_price"] or 0),
            "status": existing_order["status"],
            "workflow_state": existing_order["workflow_state"]
        }

    order_name = repo.create_sell_now_order(payload, assessment)

    final_price = float(assessment["estimated_price"] or 0)

    return {
        "success": True,
        "message": "Sell now order created successfully",
        "order_name": order_name,
        "assessment_name": assessment["name"],
        "customer_id": assessment["customer"],
        "item_code": assessment["item"],
        "item_name": assessment["item_name"],
        "final_price": round(final_price, 2),
        "approved_price": round(final_price, 2),
        "status": "Draft",
        "workflow_state": "Draft"
    }


def create_appointment_service(payload: dict):
    """
    Books a pickup appointment for an assessment.

    This creates ONLY the appointment. It never creates a Buyback Order.
    If an order already exists for the assessment (made by SellNow), the
    appointment is linked to it; otherwise buyback_order stays empty.
    """
    assessment = repo.get_assessment_for_sell_now(payload["assessment_name"])
    if not assessment:
        return {
            "success": False,
            "message": "Assessment not found",
            "data": []
        }

    if (assessment.get("customer") or "") != payload["customer_id"]:
        return {
            "success": False,
            "message": "Assessment does not belong to this customer",
            "data": []
        }

    price = round(float(payload["price"]), 2)

    order = repo.get_order_by_assessment(payload["assessment_name"])
    order_name = order["name"] if order else None

    existing = repo.get_open_appointment(
        customer_id=assessment["customer"],
        order_name=order_name,
        assessment_name=assessment["name"],
        appointment_date=payload.get("appointment_date"),
        appointment_slot=payload.get("appointment_slot")
    )

    if existing:
        return {
            "success": True,
            "message": "Appointment already exists",
            "appointment_name": existing["name"],
            "appointment_id": existing["appointment_id"],
            "order_name": existing.get("buyback_order"),
            "assessment_name": assessment["name"],
            "customer_id": assessment["customer"],
            "status": existing["status"],
            "appointment_date": str(existing["appointment_date"]) if existing["appointment_date"] else None,
            "appointment_slot": existing["appointment_slot"]
        }

    if payload.get("store_id") and not payload.get("store_name"):
        payload["store_name"] = repo.get_store_name(payload["store_id"])

    appointment_name = repo.create_pickup_appointment(payload, assessment, order_name, price)

    return {
        "success": True,
        "message": "Appointment created successfully",
        "appointment_name": appointment_name,
        "order_name": order_name,
        "assessment_name": assessment["name"],
        "customer_id": assessment["customer"],
        "customer_name": assessment.get("customer_name"),
        "item_code": assessment.get("item"),
        "item_name": assessment.get("item_name"),
        "price": price,
        "status": "Scheduled",
        "store_id": payload.get("store_id"),
        "store_name": payload.get("store_name"),
        "appointment_type": payload.get("appointment_type"),
        "appointment_date": payload.get("appointment_date"),
        "appointment_slot": payload.get("appointment_slot")
    }
