"""
Buyback pricing, following the ERP's calculate_estimated_price.

    1. Dead phone: the Phone Dead price of the Buyback Price Master,
       grade F. Nothing else is calculated.
    2. Warranty status and device age are required. They choose the
       price band of the Buyback Price Master:
           iw_0_3    in warranty, up to 3 months old
           iw_0_6    in warranty, up to 6 months old
           iw_6_11   in warranty, up to 11 months old
           oow_11    everything else: out of warranty, or older than 11 months
    3. Grade: the worst "Forces Grade" among the answered grading
       questions. Grade A when no answer forces a grade.
    4. Base price: the Price Master cell {grade}_grade_{band}. A grade
       the band has no column for (D in the 0 to 3 months band) takes
       the price of the worst grade the band has.
    5. Deductions: every answer's percent of the BASE price (the Apple
       percent for Apple phones; a question for the other brand family
       costs nothing). One deduction per fault: when the same fault is
       reported twice, only the largest deduction counts.
    6. Pricing rules: every Buyback Pricing Rule that fits the phone
       (brand, item group, grade, warranty, age) adds its deduction:
       a flat amount, a percent of the base price, or a slab percent.
    7. Cap: Buyback Settings "max_total_deduction_percent", 100 when empty.
    8. Floor: the scrap price, when the Price Master has one. A phone
       priced at scrap gets grade E.

This module has no database code.
"""
import re

GRADES = ("A", "B", "C", "D")          # best to worst
SCRAP_GRADE = "E"
DEAD_GRADE = "F"
ALL_GRADES = GRADES + (SCRAP_GRADE, DEAD_GRADE)

BANDS = (
    ("iw_0_3", "In warranty, up to 3 months"),
    ("iw_0_6", "In warranty, up to 6 months"),
    ("iw_6_11", "In warranty, up to 11 months"),
    ("oow_11", "Out of warranty, or older than 11 months"),
)
BAND_LABELS = dict(BANDS)
DEFAULT_BAND_GRADES = {"iw_0_3": ("A", "B", "C")}      # the 0 to 3 months band has no D column

DEFAULT_MAX_DEDUCTION_PERCENT = 100.0
MAX_AGE_MONTHS = 600                    # 50 years; a larger age is treated as not understood

IN_WARRANTY_TEXT = "In Warranty"
OUT_OF_WARRANTY_TEXT = "Out of Warranty"
APPLE_FAMILY = "Apple"
ANDROID_FAMILY = "Android"
GRADING_PURPOSE = "Grading"

_NEGATIVE_WORDS = {"out", "oow", "expired", "not", "no", "without", "false", "0"}
_POSITIVE_WORDS = {"in", "iw", "under", "yes", "true", "1", "active", "valid"}


def num(value):
    """10000.0 -> '10000', 166.5 -> '166.5'"""
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return text or "0"


def _key(value):
    value = getattr(value, "value", value)
    return str(value if value is not None else "").strip().lower()


def _blank(value):
    return _key(value) in ("", "any", "all")


def _number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------- inputs
def parse_warranty(value):
    """True = in warranty, False = out of warranty, None = not understood."""
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    value = getattr(value, "value", value)
    words = re.sub(r"[^a-z0-9]+", " ", str(value).lower()).split()

    if not words:
        return None

    if words == ["y"]:
        return True

    if words == ["n"]:
        return False

    if any(word in _NEGATIVE_WORDS for word in words):
        return False

    if any(word in _POSITIVE_WORDS for word in words):
        return True

    return None


def resolve_age_months(value):
    """
    Age in months as a number, like the ERP's _resolve_age_months.

    A number is used as it is (14, "14"). A range answer gives its
    middle, rounded up: "0-3 Months" -> 2, "4-6 Months" -> 5,
    "7-11 Months" -> 9. "12+ Months" gives 14. "Up to 3 months" -> 3.
    None when it was not sent or not understood.
    """
    if value is None or value == "":
        return None

    value = getattr(value, "value", value)

    try:
        age = float(value)
    except (TypeError, ValueError):
        text = str(value).strip().lower()
        numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)]

        if not numbers:
            return None

        if len(numbers) >= 2:
            age = float(int((numbers[0] + numbers[1]) / 2 + 0.5))     # a range: its middle, rounded up
        elif "+" in text or any(word in text for word in ("more", "above", "over")):
            age = numbers[0] + 2                                      # "12+", "more than 12"
        else:
            age = numbers[0]                                          # "up to 3 months", "9 months"

    # also false for "nan" and "inf", which float() accepts
    return age if 0 <= age <= MAX_AGE_MONTHS else None


def parse_grade(value):
    """'A', 'Grade B', 'C Grade', 'd' -> the grade letter. Anything else -> None."""
    if value is None:
        return None

    text = str(value).strip().upper()

    if text in ALL_GRADES:
        return text

    found = re.search(r"GRADE\s*[-:]?\s*([A-F])\b|\b([A-F])\s*[- ]?\s*GRADE", text)
    if found:
        return found.group(1) or found.group(2)

    return None


def family_from_brand(brand):
    """'Apple' for Apple phones, else 'Android' (the ERP's two brand families)."""
    text = str(brand or "").lower()
    return APPLE_FAMILY if "apple" in text or "iphone" in text else ANDROID_FAMILY


def family_allowed(applies_to, family):
    """
    The ERP's applies_to_brand_family check on a question: "Any" or empty
    means every phone; otherwise the question only costs on its own family.
    """
    only = _key(applies_to)

    if only in ("", "any"):
        return True

    if only in ("apple", "ios", "iphone"):
        return family == APPLE_FAMILY

    if only == "android":
        return family == ANDROID_FAMILY

    return False


# ---------------------------------------------------------------- band and prices
def resolve_band(in_warranty, age_months):
    """The Price Master band, exactly as the ERP's _resolve_bucket."""
    if in_warranty and age_months is not None:
        if age_months <= 3:
            return "iw_0_3"
        if age_months <= 6:
            return "iw_0_6"
        if age_months <= 11:
            return "iw_6_11"

    return "oow_11"


def column(grade, band):
    return f"{grade.lower()}_grade_{band}"


def cell_price(price_row, grade, band):
    """One cell of the Price Master. None when it is empty or zero."""
    value = _number((price_row or {}).get(column(grade, band)))
    return value if value > 0 else None


def band_grades(price_row, band):
    """The grades the band has a column for (the 0 to 3 months band has no D)."""
    found = tuple(grade for grade in GRADES if column(grade, band) in (price_row or {}))
    return found or DEFAULT_BAND_GRADES.get(band, GRADES)


def band_prices(price_row, band):
    """{"A": 7800.0, "B": 7410.0, "C": 7040.0, "D": 4928.0} for one band."""
    return {grade: cell_price(price_row, grade, band) for grade in GRADES}


def price_table(price_row):
    """The whole grade table of one phone, for showing to the app."""
    table = {}

    for band, label in BANDS:
        table[band] = {"label": label, **band_prices(price_row, band)}

    return table


def base_price(price_row, grade, band):
    """
    (price, grade whose price it is), like the ERP's _get_base_price:
    a grade the band has no column for takes the band's worst grade.
    """
    available = band_grades(price_row, band)
    used = grade if grade in available else available[-1]
    return cell_price(price_row, used, band), used


def special_price(price_row, kind):
    """The scrap price or the Phone Dead price (kind = "scrap_price" / "phone_dead_price"), None when empty."""
    value = _number((price_row or {}).get(kind))
    return value if value > 0 else None


# ---------------------------------------------------------------- grade
def worst_grade(grades):
    return max(grades, key=GRADES.index)


def grade_from_answers(answers):
    """
    The worst "Forces Grade" among the answered grading questions, like
    the ERP's resolve_grade_from_answers. Grade A when none forces one.

    answers: [(question_id, answer_value, info)], info being the question's
             data from the repository (None when the question was not found).

    Returns (grade, [(question_id, answer_value, grade), ...]).
    """
    forced = []

    for question_id, answer, info in answers:
        info = info or {}

        if info.get("disabled") or not info.get("grading", True):
            continue

        grade = parse_grade((info.get("forces_grade") or {}).get(_key(answer)))

        if grade in GRADES:
            forced.append((question_id, answer, grade))

    if not forced:
        return "A", []

    return worst_grade([grade for _, _, grade in forced]), forced


# ---------------------------------------------------------------- deductions
def find_option(info, answer):
    """The option of a question that matches an answer (case and spaces ignored)."""
    wanted = _key(answer)

    for option in (info or {}).get("options", []):
        if _key(option.get("value")) == wanted:
            return option

    return None


def rate_for_family(option, family):
    """The Apple percent for Apple phones when it is set, else the standard percent."""
    if family == APPLE_FAMILY and _number(option.get("apple_percent")):
        return _number(option["apple_percent"])

    return _number(option.get("percent"))


def deduction_line(kind, question_id, answer, info, base, family):
    """
    One answer as a deduction line, like the ERP's _get_question_deduction.
    "skipped" says why a valid answer costs nothing: "disabled" or "family".
    """
    option = find_option(info, answer)
    skipped = None

    if option is not None and (info or {}).get("disabled"):
        skipped = "disabled"
    elif option is not None and not family_allowed((info or {}).get("brand_family"), family):
        skipped = "family"

    percent = abs(rate_for_family(option, family)) if option and not skipped else 0.0
    fault_code = _key((info or {}).get("fault_code") or (option or {}).get("fault_code"))

    return {
        "type": kind,
        "question_id": str(question_id),
        "question_text": (info or {}).get("question_text"),
        "answer_value": None if answer is None else str(getattr(answer, "value", answer)),
        "found": info is not None,
        "matched": option is not None,
        "skipped": skipped,
        "percent": percent,
        "amount": abs(base * percent / 100) if percent else 0.0,
        "fault_code": fault_code or None,
        # one deduction per fault: the same fault code, or the same question
        "key": f"fault:{fault_code}" if fault_code else f"question:{question_id}",
        "counted": False,
    }


def keep_largest(lines):
    """Marks the largest deduction per fault as counted, like the ERP's _collect_deduction."""
    best = {}

    for line in lines:
        if line["amount"] and (line["key"] not in best or line["amount"] > best[line["key"]]["amount"]):
            best[line["key"]] = line

    for line in lines:
        line["counted"] = line["amount"] > 0 and best.get(line["key"]) is line

    return lines


def clamp(total, base, max_percent):
    """(capped total, limit used), like the ERP's _clamp_deductions."""
    percent = _number(max_percent) or DEFAULT_MAX_DEDUCTION_PERCENT
    percent = max(0.0, min(percent, 100.0))
    return min(total, base * percent / 100.0), percent


# ---------------------------------------------------------------- pricing rules
# A Buyback Pricing Rule fits a phone when every filter it has a value for
# matches. These are the filter columns looked for on the rule row.
RULE_GRADE_COLUMNS = ("grade", "grade_letter", "applies_to_grade")
RULE_WARRANTY_COLUMNS = ("warranty_status",)
RULE_AGE_RANGES = (
    ("min_age_months", "max_age_months"), ("from_age_months", "to_age_months"),
    ("min_device_age_months", "max_device_age_months"), ("device_age_from", "device_age_to"),
    ("age_from", "age_to"),
)
RULE_AGE_TEXT_COLUMNS = ("device_age_months", "device_age", "age_band")


def age_in_text(text, age_months):
    """True when an age falls in a text such as '7-11 Months', '12+ Months', 'Up to 3 months' or '9'."""
    numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text or "")]
    lower = str(text or "").lower()

    if not numbers:
        return False

    if len(numbers) >= 2:
        return numbers[0] <= age_months <= numbers[1]

    limit = numbers[0]
    more = "+" in lower or ">" in lower or any(w in lower for w in ("above", "more", "over"))
    less = "<" in lower or any(w in lower for w in ("below", "less", "under", "up to", "upto"))

    if more:
        return age_months >= limit
    if less:
        return age_months <= limit
    return limit == age_months


def rule_applies(row, brand, item_group, grade, in_warranty, age_months):
    """Whether one Buyback Pricing Rule row fits this phone."""
    for column_name, value in (("brand", brand), ("item_group", item_group)):
        if not _blank(row.get(column_name)) and _key(row[column_name]) != _key(value):
            return False

    for column_name in RULE_GRADE_COLUMNS:
        wanted = parse_grade(row.get(column_name)) if not _blank(row.get(column_name)) else None
        if wanted and wanted != grade:
            return False

    for column_name in RULE_WARRANTY_COLUMNS:
        wanted = parse_warranty(row.get(column_name)) if not _blank(row.get(column_name)) else None
        if wanted is not None and wanted != bool(in_warranty):
            return False

    for low, high in RULE_AGE_RANGES:
        if _number(row.get(low)) > 0 and age_months < _number(row.get(low)):
            return False
        if _number(row.get(high)) > 0 and age_months > _number(row.get(high)):
            return False

    for column_name in RULE_AGE_TEXT_COLUMNS:
        if not _blank(row.get(column_name)) and not age_in_text(str(row[column_name]), age_months):
            return False

    return True


def rule_amount(row, slabs, base):
    """The rule's deduction, exactly as the ERP's calculate_deduction."""
    kind = _key(row.get("rule_type"))

    if kind == "flat deduction":
        return _number(row.get("flat_deduction"))

    if kind == "percentage deduction":
        return base * _number(row.get("percent_deduction")) / 100

    if kind == "slab-based" and slabs:
        for slab in sorted(slabs, key=lambda s: _number(s.get("from_amount"))):
            if _number(slab.get("from_amount")) <= base <= _number(slab.get("to_amount")):
                return base * _number(slab.get("deduction_percent")) / 100
        return 0.0

    return 0.0


def rule_line(rule, base):
    """A pricing rule as a deduction line, or None when it deducts nothing."""
    row = rule.get("row") or {}
    amount = rule_amount(row, rule.get("slabs") or [], base)

    if not amount:
        return None

    name = str(row.get("name") or "")
    label = row.get("rule_name") or row.get("title") or name

    return {
        "type": "rule",
        "question_id": name,
        "question_text": str(label),
        "answer_value": row.get("rule_type"),
        "found": True,
        "matched": True,
        "skipped": None,
        "percent": amount / base * 100 if base else 0.0,
        "amount": amount,
        "fault_code": None,
        "key": f"rule:{name}",
        "counted": True,
    }


# ---------------------------------------------------------------- the whole calculation
def calculate(price_row, in_warranty, age_months, items, family, max_percent,
              is_phone_dead=False, item_code="", rules=None, brand=None, item_group=None):
    """
    The ERP's calculate_estimated_price for one phone.

    items: [(kind, question_id, answer_value, info)] for the answered ERP
           questions ("question") and tests ("diagnostic"); info is the
           question's data from the repository, None when not found.
    rules: the ERP's active Buyback Pricing Rules, from the repository.

    Returns a dict with the price and every step, or {"error": text}
    where the ERP would stop with an error.
    """
    band = None
    if in_warranty is not None and age_months is not None:
        band = resolve_band(in_warranty, age_months)

    where = ""
    if in_warranty is not None:
        where = "In warranty" if in_warranty else "Out of warranty"
        where += f", age counted as {num(age_months)} months. " if age_months is not None else ", age not given. "
    if band:
        where += f"Price band: {BAND_LABELS[band]}. "

    result = {
        "mode": "grade",
        "band": band,
        "band_label": BAND_LABELS.get(band),
        "in_warranty": in_warranty,
        "age_months": age_months,
        "grade_prices": band_prices(price_row, band) if band else None,
        "grade": "A",
        "price_grade": "A",
        "forced": [],
        "lines": [],
        "raw_total": 0.0,
        "capped_total": 0.0,
        "max_percent": DEFAULT_MAX_DEDUCTION_PERCENT,
        "cap_applied": False,
        "scrap_price": None,
        "is_scrap": False,
        "is_phone_dead": bool(is_phone_dead),
    }

    # 1. dead phone: its own price, grade F, nothing else is calculated
    if is_phone_dead:
        dead_price = special_price(price_row, "phone_dead_price")

        if not dead_price:
            return {"error": f"No Phone Dead price is configured for {item_code}"}

        result.update({
            "mode": "dead",
            "grade": DEAD_GRADE,
            "price_grade": DEAD_GRADE,
            "base_price": dead_price,
            "calculated_price": dead_price,
            "final_price": dead_price,
            "explanation": (
                f"{where}The phone is dead, so the Phone Dead price is used: "
                f"{num(dead_price)}, grade F."
            ),
        })
        return result

    # 2. the band needs both inputs
    if band is None:
        return {"error": "warranty_status and device_age_months are required"}

    # 3. grade from the grading answers
    answers = [(qid, answer, info) for kind, qid, answer, info in items if kind == "question"]
    grade, forced = grade_from_answers(answers)

    # 4. base price: one cell of the Price Master
    base, price_grade = base_price(price_row, grade, band)

    if not base:
        return {"error": f"No Grade {price_grade} price is configured for {item_code} in the {band} band"}

    explanation = where

    if forced:
        question_id, answer, _ = max(forced, key=lambda item: GRADES.index(item[2]))
        explanation += f"Answer '{answer}' on {question_id} sets grade {grade}. "
    else:
        explanation += "No answer forces a lower grade, so the grade is A. "

    if price_grade != grade:
        explanation += f"This band has no {grade} grade price, so the {price_grade} grade price is used. "

    explanation += f"Base price: {num(base)} ({price_grade} grade). "

    # 5. deductions: percent of the base price, one per fault
    lines = keep_largest([deduction_line(kind, qid, answer, info, base, family) for kind, qid, answer, info in items])
    counted = [line for line in lines if line["counted"]]
    dropped = [line for line in lines if line["amount"] and not line["counted"]]
    answer_total = sum(line["amount"] for line in counted)

    if counted:
        explanation += (
            f"Deductions: {num(answer_total / base * 100)}% of {num(base)} = {num(answer_total)} "
            f"({len(counted)} answer{'' if len(counted) == 1 else 's'}). "
        )
    else:
        explanation += "No deductions from the answers. "

    if dropped:
        explanation += (
            f"{len(dropped)} deduction{' was' if len(dropped) == 1 else 's were'} dropped "
            f"because the same fault was already counted. "
        )

    # 6. pricing rules on top
    rule_lines = [
        line for line in (
            rule_line(rule, base) for rule in (rules or [])
            if rule_applies(rule.get("row") or {}, brand, item_group, grade, in_warranty, age_months)
        )
        if line
    ]
    lines.extend(rule_lines)
    rule_total = sum(line["amount"] for line in rule_lines)

    if rule_lines:
        names = ", ".join(line["question_text"] for line in rule_lines)
        explanation += f"Pricing rule{'' if len(rule_lines) == 1 else 's'} {names}: {num(rule_total)} more. "

    raw_total = answer_total + rule_total

    # 7. cap
    capped_total, percent_limit = clamp(raw_total, base, max_percent)
    cap_applied = raw_total > capped_total

    if cap_applied:
        explanation += (
            f"The limit is {num(percent_limit)}% of the base price ({num(capped_total)}), "
            f"so {num(capped_total)} was deducted. "
        )

    calculated = base - capped_total
    explanation += f"{num(base)} minus {num(capped_total)} is {num(calculated)}. "

    # 8. floor at the scrap price
    scrap = special_price(price_row, "scrap_price")
    is_scrap = bool(scrap) and calculated < scrap
    final = scrap if is_scrap else calculated

    if is_scrap:
        explanation += (
            f"That is below the scrap price {num(scrap)}, so the estimated price is "
            f"{num(final)} and the grade is {SCRAP_GRADE}."
        )
    else:
        explanation += f"The estimated price is {num(final)}."

    result.update({
        "mode": "scrap" if is_scrap else "grade",
        "grade": SCRAP_GRADE if is_scrap else grade,
        "price_grade": price_grade,
        "forced": forced,
        "lines": lines,
        "base_price": base,
        "raw_total": raw_total,
        "rule_total": rule_total,
        "capped_total": capped_total,
        "max_percent": percent_limit,
        "cap_applied": cap_applied,
        "calculated_price": calculated,
        "scrap_price": scrap,
        "is_scrap": is_scrap,
        "final_price": final,
        "explanation": explanation,
    })
    return result


# ---------------------------------------------------------------- ERP values
def split_options(options_text):
    """A Select field's options, as the ERP stores them (one per line)."""
    return [line.strip() for line in str(options_text or "").split("\n") if line.strip()]


def erp_grade_value(options, grade):
    """The ERP dropdown value that means this grade, or the letter itself."""
    for option in options or []:
        if parse_grade(option) == grade:
            return option

    return grade


def erp_warranty_value(options, in_warranty):
    """The ERP dropdown value that means this warranty status."""
    for option in options or []:
        if parse_warranty(option) is bool(in_warranty):
            return option

    return IN_WARRANTY_TEXT if in_warranty else OUT_OF_WARRANTY_TEXT


def erp_age_value(options, age_months, sent=None):
    """
    The ERP value for the device age. With a dropdown such as
    '0-3 Months / 4-6 Months / 7-11 Months / 12+ Months' the option the
    app sent, or the one that holds the age, is returned; otherwise the
    number of months as a whole number.
    """
    for option in options or []:
        if sent is not None and _key(option) == _key(sent):
            return option

    for option in options or []:
        if age_in_text(option, age_months):
            return option

    return str(int(round(age_months)))


# ---------------------------------------------------------------- the "Warranty" questions
# GetBuybackQuestionsByItem shows these two as a normal question category,
# so the app can ask them like every other question. They are not rows of
# the ERP Question Bank: their answers only choose the price band.
WARRANTY_CATEGORY = "Warranty"
WARRANTY_QUESTION = "WARRANTY_STATUS"
AGE_QUESTION = "DEVICE_AGE"

DEFAULT_WARRANTY_OPTIONS = (IN_WARRANTY_TEXT, OUT_OF_WARRANTY_TEXT)
DEFAULT_AGE_OPTIONS = ("0-3 Months", "4-6 Months", "7-11 Months", "12+ Months")

_PRICING_INPUT_NAMES = {
    "warranty_status": "warranty",
    "device_age": "age",
    "device_age_months": "age",
}


def pricing_input_kind(identifier):
    """'warranty' or 'age' when a question name / code is one of the two Warranty questions."""
    if not identifier:
        return None

    return _PRICING_INPUT_NAMES.get(str(identifier).strip().lower())


def is_erp_warranty_question(question_code, question_text):
    """True for the ERP's own Yes/No warranty question (the ERP spells it 'Warrenty')."""
    label = f"{question_code or ''} {question_text or ''}".lower()
    return "warrant" in label or "warrent" in label


def pricing_questions(warranty_options=None, age_options=None):
    """
    The two Warranty questions, in the same shape as the ERP questions.
    The options are the ERP's own dropdown values when they are given.
    """
    def option(value):
        return {"OptionLabel": value, "OptionValue": value, "PriceImpactPercent": 0.0}

    warranty_options = list(warranty_options or [])
    age_options = list(age_options or [])

    if len(warranty_options) < 2:
        warranty_options = list(DEFAULT_WARRANTY_OPTIONS)

    if len(age_options) < 2:
        age_options = list(DEFAULT_AGE_OPTIONS)

    return [
        {
            "QuestionName": WARRANTY_QUESTION,
            "DiagnosisType": "Pricing Input",
            "QuestionID": -1,
            "QuestionText": "Is the device under warranty?",
            "QuestionCode": "warranty_status",
            "QuestionType": "Single Select",
            "Mandatory": "Yes",
            "Disabled": "No",
            "Options": [option(value) for value in warranty_options]
        },
        {
            "QuestionName": AGE_QUESTION,
            "DiagnosisType": "Pricing Input",
            "QuestionID": -2,
            "QuestionText": "How old is the device?",
            "QuestionCode": "device_age_months",
            "QuestionType": "Single Select",
            "Mandatory": "Yes",
            "Disabled": "No",
            "Options": [option(value) for value in age_options]
        }
    ]
