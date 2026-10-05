from repositories.buyback_repository import BuybackRepository
from services import grade_pricing as gp

repo = BuybackRepository()


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


# =========================================================
# PRICE HELPERS (shared by API 1 and API 2)
# =========================================================
MAX_DEDUCTION_PERCENT = 80


def _plain(value):
    """TestResult.YES -> 'Yes'; any other value is returned unchanged."""
    return getattr(value, "value", value)


def _norm(value):
    value = _plain(value)
    return str(value if value is not None else "").strip().lower()


def _num(value):
    """10000.0 -> '10000', 166.5 -> '166.5'"""
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return text or "0"


def _load_question_options(question_ids):
    """
    Options of the answered questions. They are used only to explain the
    price. If this lookup fails the price is still calculated as before.
    """
    try:
        return repo.get_question_options(question_ids)
    except Exception:
        return None


def _breakdown_item(kind, question_id, tried_values, percent, options, warnings):
    """One line of the price breakdown. Adds a warning when the answer was ignored."""
    sent = _plain(tried_values[0]) if tried_values else None
    info = options.get(question_id)

    if percent:
        matched = True
    elif info is None:
        matched = False
        warnings.append(
            f"{question_id}: this question was not found, so it was counted as 0%"
        )
    else:
        valid = {_norm(value) for value, _ in info["options"]}
        matched = any(_norm(value) in valid for value in tried_values)

        if not matched:
            allowed = ", ".join(str(value) for value, _ in info["options"])
            warnings.append(
                f"{question_id}: answer '{sent}' is not one of [{allowed}], "
                f"so it was counted as 0%"
            )

    return {
        "type": kind,
        "question_id": str(question_id),
        "question_text": info.get("question_text") if info else None,
        "answer_value": None if sent is None else str(sent),
        "price_impact_percent": round(float(percent or 0), 2),
        "matched": matched
    }


def _duplicate_warnings(question_ids, warnings):
    counts = {}

    for question_id in question_ids:
        counts[question_id] = counts.get(question_id, 0) + 1

    for question_id, count in counts.items():
        if count > 1:
            warnings.append(
                f"{question_id} was answered {count} times and every answer was counted"
            )


def _price_from_percent(base_price, raw_percent, floor_price):
    """
    base price - deduction %, with two limits:
      - the deduction is never more than MAX_DEDUCTION_PERCENT
      - the price is never below the floor price
    """
    total_percent = min(raw_percent, MAX_DEDUCTION_PERCENT)
    calculated_price = base_price * (1 - total_percent / 100)
    final_price = max(floor_price, calculated_price)

    cap_applied = raw_percent > MAX_DEDUCTION_PERCENT
    floor_applied = calculated_price < floor_price

    explanation = f"Deductions add up to {_num(raw_percent)}%. "

    if cap_applied:
        explanation += (
            f"The limit is {MAX_DEDUCTION_PERCENT}%, "
            f"so {MAX_DEDUCTION_PERCENT}% was used. "
        )

    explanation += (
        f"{_num(base_price)} minus {_num(total_percent)}% "
        f"is {_num(calculated_price)}. "
    )

    if floor_applied:
        explanation += (
            f"That is below the floor price {_num(floor_price)}, "
            f"so the estimated price is {_num(final_price)}."
        )
    else:
        explanation += f"The estimated price is {_num(final_price)}."

    return {
        "total_percent": total_percent,
        "calculated_price": calculated_price,
        "final_price": final_price,
        "cap_applied": cap_applied,
        "floor_applied": floor_applied,
        "explanation": explanation
    }


# =========================================================
# GRADE-WISE PRICING (ERP PRICE MASTER)
# =========================================================
def _take_pricing_inputs(payload):
    """
    The app answers the "Warranty" category like any other question:
        {"question_id": "WARRANTY_STATUS", "answer_value": "Out of Warranty"}
        {"question_id": "DEVICE_AGE", "answer_value": "11+ months"}

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


def _wants_grade_pricing(payload):
    """Grade-wise pricing is used only when the client sends warranty or age."""
    return (
        payload.get("warranty_status") not in (None, "")
        or payload.get("device_age_months") is not None
    )


def _answer_warranty(responses, options):
    """Warranty status from the ERP's own warranty question, when it was answered."""
    for r in responses:
        info = (options or {}).get(r.get("question_id")) or {}

        if gp.is_erp_warranty_question(info.get("question_code"), info.get("question_text")):
            answer = gp.parse_warranty(r.get("answer_value"))
            if answer is not None:
                return answer

    return None


def _forced_grades(responses, options):
    """[(question_id, answer, grade)] for answers the ERP marks with Forces Grade."""
    forced = []

    for r in responses:
        info = (options or {}).get(r.get("question_id")) or {}
        marks = info.get("forces_grade") or {}
        grade = gp.parse_grade(marks.get(_norm(r.get("answer_value"))))

        if grade:
            forced.append((r.get("question_id"), _plain(r.get("answer_value")), grade))

    return forced


def _grade_price(payload, responses, options, raw_percent, warnings):
    """
    The grade-wise price from the ERP Price Master.
    Returns None when it cannot be used; the caller then uses the percent price.
    """
    try:
        price_row = repo.get_price_row(payload["item_code"])
    except Exception:
        price_row = None

    if not price_row:
        warnings.append("Grade prices could not be read, so the percent price was used")
        return None

    sent_age = payload.get("device_age_months")
    age = gp.parse_age_months(sent_age)

    if sent_age not in (None, "") and age is None:
        warnings.append(
            f"device_age_months '{sent_age}' was not understood. "
            f"Send the age in months, for example 14"
        )

    sent_warranty = payload.get("warranty_status")
    in_warranty = gp.parse_warranty(sent_warranty)

    if sent_warranty not in (None, "") and in_warranty is None:
        warnings.append(
            f"warranty_status '{sent_warranty}' was not understood. "
            f"Send '{gp.IN_WARRANTY_TEXT}' or '{gp.OUT_OF_WARRANTY_TEXT}'"
        )

    if in_warranty is None:
        in_warranty = _answer_warranty(responses, options)

    if in_warranty is None and age is not None:
        try:
            months = repo.get_item_default_warranty_months(payload["item_code"])
        except Exception:
            months = None

        months = months or gp.DEFAULT_WARRANTY_MONTHS
        in_warranty = age < months

        warnings.append(
            f"warranty_status was not sent, so it was worked out from the age: "
            f"{'in' if in_warranty else 'out of'} warranty "
            f"(warranty period {gp.num(months)} months)"
        )

    if in_warranty is None:
        warnings.append(
            "Warranty status and device age are both missing, "
            "so the percent price was used"
        )
        return None

    if in_warranty and age is None:
        warnings.append(
            "device_age_months was not sent, so the 6 to 11 months band was used"
        )

    result = gp.grade_price(
        price_row,
        raw_percent,
        in_warranty,
        age,
        _forced_grades(responses, options),
        MAX_DEDUCTION_PERCENT
    )

    if result is None:
        warnings.append(
            "This phone has no grade prices in the Price Master, "
            "so the percent price was used"
        )

    return result


def _save_grade_info(assessment_name, grade, warnings):
    """Writes grade, warranty and age on the assessment, in the ERP's own dropdown words."""
    try:
        selects = repo.get_doctype_select_options(
            "Buyback Assessment",
            ["estimated_grade", "warranty_status", "device_age_months"]
        )
    except Exception:
        selects = {}

    values = {
        "estimated_grade": gp.erp_grade_value(
            selects.get("estimated_grade"), grade["grade"]
        ),
        "warranty_status": gp.erp_warranty_value(
            selects.get("warranty_status"), grade["in_warranty"]
        )
    }

    if grade["age_months"] is not None:
        values["device_age_months"] = gp.erp_age_value(
            selects.get("device_age_months"), grade["age_months"]
        )

    try:
        repo.set_assessment_grade_info(assessment_name, values)
    except Exception:
        warnings.append(
            "The price was saved, but grade, warranty and age "
            "could not be saved on the assessment"
        )


def _build_result(payload, base_price, responses, options, response_percent,
                  diagnostic_percent, breakdown, warnings, save):
    """Shared end of API 1 and API 2: work out the price, save, build the reply."""
    raw_percent = response_percent + (diagnostic_percent or 0)

    # FLOOR (percent pricing)
    floor_price = repo.get_floor_price(payload["item_code"])
    if not floor_price or floor_price <= 0:
        floor_price = base_price * 0.1

    grade = None
    if _wants_grade_pricing(payload):
        grade = _grade_price(payload, responses, options, raw_percent, warnings)

    if grade:
        # GRADE-WISE: the price is one cell of the ERP grade table
        price = grade
        base_price = grade["base_price"]
        floor_price = grade["floor_price"]
    else:
        # PERCENT: base price minus the deductions, with cap and floor
        price = _price_from_percent(base_price, raw_percent, floor_price)

    # SAVE
    name = save(payload, price["final_price"])

    if grade:
        _save_grade_info(name, grade, warnings)

    result = {
        "success": True,
        "assessment_name": name,
        "base_price": round(base_price, 2),
        "total_percent": round(price["total_percent"], 2),
        "calculated_price": round(price["calculated_price"], 2),
        "floor_price": round(floor_price, 2),
        "estimated_price": round(price["final_price"], 2),
        "raw_percent": round(raw_percent, 2),
        "response_percent": round(response_percent, 2),
        "cap_applied": price["cap_applied"],
        "floor_applied": price["floor_applied"],
        "price_explanation": price["explanation"],
        "pricing_mode": "grade" if grade else "percent",
        "estimated_grade": grade["grade"] if grade else None,
        "price_band": grade["band"] if grade else None,
        "price_band_label": grade["band_label"] if grade else None,
        "warranty_status": (
            (gp.IN_WARRANTY_TEXT if grade["in_warranty"] else gp.OUT_OF_WARRANTY_TEXT)
            if grade else None
        ),
        "device_age_months": grade["age_months"] if grade else None,
        "grade_prices": grade["grade_prices"] if grade else None,
        "breakdown": breakdown,
        "warnings": warnings
    }

    if diagnostic_percent is not None:
        result["diagnostic_percent"] = round(diagnostic_percent, 2)

    return result


# =========================================================
# API 1: CREATE BASIC ASSESSMENT (RESPONSES ONLY)
# =========================================================
def create_buyback_service(payload: dict):

    payload = _take_pricing_inputs(payload)

    price_data = repo.get_base_price(payload["item_code"])

    if not price_data or price_data.get("current_market_price") is None:
        return {"success": False, "message": "Price not found"}

    base_price = float(price_data["current_market_price"])

    responses = payload.get("responses", [])
    options = _load_question_options([r.get("question_id") for r in responses])

    breakdown = []
    warnings = []

    if options is None:
        warnings.append("Answer details could not be loaded, so the breakdown is empty")

    # RESPONSE %
    response_percent = 0

    for r in responses:
        percent = repo.get_price_percent(
            r.get("question_id"),
            r.get("answer_value")
        )
        response_percent += percent

        if options is not None:
            breakdown.append(_breakdown_item(
                "question",
                r.get("question_id"),
                [r.get("answer_value")],
                percent,
                options,
                warnings
            ))

    _duplicate_warnings([r.get("question_id") for r in responses], warnings)

    return _build_result(
        payload, base_price, responses, options, response_percent,
        None, breakdown, warnings, repo.create_assessment
    )


# =========================================================
# API 2: CREATE FULL ASSESSMENT (RESP + DIAGNOSTICS)
# =========================================================
def create_full_buyback_service(payload: dict):

    payload = _take_pricing_inputs(payload)

    price_data = repo.get_base_price(payload["item_code"])

    if not price_data or price_data.get("current_market_price") is None:
        return {"success": False, "message": "Price not found"}

    base_price = float(price_data["current_market_price"])

    responses = payload.get("responses", [])
    diagnostics = payload.get("diagnostics", [])

    options = _load_question_options(
        [r.get("question_id") for r in responses]
        + [d.get("test_code") for d in diagnostics]
    )

    breakdown = []
    warnings = []

    if options is None:
        warnings.append("Answer details could not be loaded, so the breakdown is empty")

    # RESPONSE %
    response_percent = 0

    for r in responses:
        percent = repo.get_price_percent(
            r.get("question_id"),
            r.get("answer_value")
        )
        response_percent += percent

        if options is not None:
            breakdown.append(_breakdown_item(
                "question",
                r.get("question_id"),
                [r.get("answer_value")],
                percent,
                options,
                warnings
            ))

    # DIAGNOSTIC %
    diagnostic_percent = 0

    for d in diagnostics:
        tried_values = _diagnostic_answer_values(d.get("result"))

        percent = repo.get_price_percent_from_values(
            d.get("test_code"),
            tried_values
        )

        diagnostic_percent += percent

        if options is not None:
            breakdown.append(_breakdown_item(
                "diagnostic",
                d.get("test_code"),
                tried_values,
                percent,
                options,
                warnings
            ))

    _duplicate_warnings(
        [r.get("question_id") for r in responses]
        + [d.get("test_code") for d in diagnostics],
        warnings
    )

    return _build_result(
        payload, base_price, responses, options, response_percent,
        diagnostic_percent, breakdown, warnings, repo.create_full_assessment
    )


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
    total_percent = 0
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

        percent = repo.get_price_percent(question["name"], answer["answer_value"])
        total_percent += percent

        saved_answers.append({
            "question_name": question["name"],
            "question_code": question["question_code"],
            "question_text": question["question_text"],
            "answer_value": answer["answer_value"],
            "price_impact_percent": percent
        })

    raw_percent = total_percent
    total_percent = min(total_percent, MAX_DEDUCTION_PERCENT)
    base_price = float(item["current_market_price"])
    calculated_price = base_price * (1 - total_percent / 100)
    floor_price = float(item["d_grade_oow_11"] or 0)

    if floor_price <= 0:
        floor_price = base_price * 0.1

    estimated_price = max(floor_price, calculated_price)

    # GRADE-WISE: only when the Warranty category was answered
    warnings = []
    grade = None

    if pricing_inputs:
        grade = _grade_price(
            {
                "item_code": payload["item_code"],
                "warranty_status": pricing_inputs.get("warranty"),
                "device_age_months": pricing_inputs.get("age")
            },
            [
                {"question_id": a["question_name"], "answer_value": a["answer_value"]}
                for a in saved_answers
            ],
            _load_question_options([a["question_name"] for a in saved_answers]),
            raw_percent,
            warnings
        )

    if grade:
        base_price = grade["base_price"]
        total_percent = grade["total_percent"]
        calculated_price = grade["calculated_price"]
        floor_price = grade["floor_price"]
        estimated_price = grade["final_price"]

    assessment_name = repo.create_mobile_answer_assessment(
        payload,
        customer,
        item,
        saved_answers,
        estimated_price
    )

    if grade:
        _save_grade_info(assessment_name, grade, warnings)

    return {
        "success": True,
        "message": "Buyback answers submitted successfully",
        "assessment_name": assessment_name,
        "customer_id": customer["name"],
        "item_code": item["item_code"],
        "answer_count": len(saved_answers),
        "base_price": round(base_price, 2),
        "total_percent": round(total_percent, 2),
        "calculated_price": round(calculated_price, 2),
        "floor_price": round(floor_price, 2),
        "final_price": round(estimated_price, 2),
        "estimated_price": round(estimated_price, 2),
        "pricing_mode": "grade" if grade else "percent",
        "estimated_grade": grade["grade"] if grade else None,
        "price_band": grade["band"] if grade else None,
        "price_band_label": grade["band_label"] if grade else None,
        "warranty_status": (
            (gp.IN_WARRANTY_TEXT if grade["in_warranty"] else gp.OUT_OF_WARRANTY_TEXT)
            if grade else None
        ),
        "device_age_months": grade["age_months"] if grade else None,
        "grade_prices": grade["grade_prices"] if grade else None,
        "price_explanation": grade["explanation"] if grade else None,
        "warnings": warnings,
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
