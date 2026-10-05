"""
Grade-wise buyback pricing, following the ERP's Buyback Price Master.

The Price Master holds one price per grade (A, B, C, D) for each
warranty / age band of a phone:

    a_grade_iw_0_3    in warranty, up to 3 months old
    a_grade_iw_0_6    in warranty, up to 6 months old
    a_grade_iw_6_11   in warranty, 6 to 11 months old
    a_grade_oow_11    out of warranty, 11 months and more

This module has no database code. It only decides:

    1. which band a phone belongs to   (from warranty status and age)
    2. which grade it gets             (from the answers)
    3. which price that gives          (read from the Price Master row)

How the grade is chosen
-----------------------
    a. If the ERP marks a chosen answer with "Forces Grade", that grade is
       used. When several answers force a grade, the worst one wins.
    b. Otherwise the answers' deduction percent is applied to the A grade
       price of the band, and the grade whose ERP price is nearest to that
       amount is used.

Rule (b) is a default. It uses only the ERP's own prices, but it is not
taken from the ERP's program code. Change `nearest_grade` to change it.
"""
import re

GRADES = ("A", "B", "C", "D")          # best to worst

BANDS = (
    ("iw_0_3", "In warranty, up to 3 months"),
    ("iw_0_6", "In warranty, up to 6 months"),
    ("iw_6_11", "In warranty, 6 to 11 months"),
    ("oow_11", "Out of warranty, 11 months and more"),
)
BAND_LABELS = dict(BANDS)

DEFAULT_WARRANTY_MONTHS = 12
MAX_AGE_MONTHS = 600                    # 50 years; a larger age is treated as not understood

IN_WARRANTY_TEXT = "In Warranty"
OUT_OF_WARRANTY_TEXT = "Out of Warranty"

_NEGATIVE_WORDS = {"out", "oow", "expired", "not", "no", "without", "false", "0"}
_POSITIVE_WORDS = {"in", "iw", "under", "yes", "true", "1", "active", "valid"}


def num(value):
    """10000.0 -> '10000', 166.5 -> '166.5'"""
    text = f"{float(value):.2f}".rstrip("0").rstrip(".")
    return text or "0"


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


def parse_age_months(value):
    """
    Age in months as a number, or None when it was not sent or not understood.

    Accepts a number (14, "14") and the answers of the device age question:
        "0-3 months"  -> 3        "3-6 months"  -> 6
        "6-11 months" -> 11       "11+ months"  -> 12
    The labels work too ("Up to 3 months", "More than 11 months").
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
            age = numbers[1]                    # a range: its upper end
        elif "+" in text or any(word in text for word in ("more", "above", "over")):
            age = numbers[0] + 1                # "11+", "more than 11"
        else:
            age = numbers[0]                    # "up to 3 months", "9 months"

    # also false for "nan" and "inf", which float() accepts
    return age if 0 <= age <= MAX_AGE_MONTHS else None


def parse_grade(value):
    """'A', 'Grade B', 'C Grade', 'd' -> the grade letter. Anything else -> None."""
    if value is None:
        return None

    text = str(value).strip().upper()

    if text in GRADES:
        return text

    found = re.search(r"GRADE\s*[-:]?\s*([ABCD])\b|\b([ABCD])\s*[- ]?\s*GRADE", text)
    if found:
        return found.group(1) or found.group(2)

    return None


# ---------------------------------------------------------------- band
def pick_band(in_warranty, age_months):
    """The Price Master band for a phone."""
    if not in_warranty:
        return "oow_11"

    if age_months is None:
        return "iw_6_11"

    if age_months <= 3:
        return "iw_0_3"

    if age_months <= 6:
        return "iw_0_6"

    return "iw_6_11"


def table_price(price_row, grade, band):
    """One cell of the Price Master. None when it is empty or zero."""
    try:
        value = float(price_row.get(f"{grade.lower()}_grade_{band}") or 0)
    except (TypeError, ValueError, AttributeError):
        return None

    return value if value > 0 else None


def grade_prices_for_band(price_row, band):
    """
    ({"A": 7800.0, "B": ...}, {"D": "iw_0_6"}) for one band.

    A grade that has no price in this band borrows the price of the same
    grade from the next older band (for example the 0 to 3 months band has
    no D grade, so D comes from the 0 to 6 months band). The second dict
    says which grades were borrowed, and from where.
    """
    order = [name for name, _ in BANDS]
    start = order.index(band)
    search = order[start:] + order[:start][::-1]

    prices = {}
    borrowed = {}

    for grade in GRADES:
        for candidate in search:
            value = table_price(price_row, grade, candidate)
            if value is not None:
                prices[grade] = value
                if candidate != band:
                    borrowed[grade] = candidate
                break

    return prices, borrowed


# ---------------------------------------------------------------- grade
def worst_grade(grades):
    return max(grades, key=GRADES.index)


def nearest_grade(prices, target_price):
    """The grade whose ERP price is closest to target_price. On a tie the lower price wins."""
    return min(prices, key=lambda grade: (abs(prices[grade] - target_price), prices[grade]))


def _available_grade(prices, wanted):
    """wanted if it has a price, else the next worse grade that has one, else the worst priced grade."""
    if wanted in prices:
        return wanted

    for grade in GRADES[GRADES.index(wanted):]:
        if grade in prices:
            return grade

    return worst_grade(list(prices))


def grade_price(price_row, raw_percent, in_warranty, age_months, forced, max_percent):
    """
    The grade-wise price of one phone.

    forced: [(question_id, answer, grade), ...] for answers the ERP marks
            with "Forces Grade".

    Returns None when the Price Master row has no A grade price to start
    from, so the caller can fall back to the percent calculation.
    """
    band = pick_band(in_warranty, age_months)
    prices, borrowed = grade_prices_for_band(price_row or {}, band)

    if "A" not in prices:
        return None

    best = "A"
    base_price = prices[best]
    floor_price = min(prices.values())

    total_percent = min(raw_percent, max_percent)
    calculated_price = base_price * (1 - total_percent / 100)
    cap_applied = raw_percent > max_percent

    explanation = "In warranty" if in_warranty else "Out of warranty"
    # "counted as": an age answer such as "11+ months" is a range, priced as 12
    explanation += f", age counted as {num(age_months)} months. " if age_months is not None else ", age not given. "
    explanation += f"Price band: {BAND_LABELS[band]}. "

    if forced:
        question_id, answer, _ = max(forced, key=lambda item: GRADES.index(item[2]))
        wanted = worst_grade([item[2] for item in forced])
        grade = _available_grade(prices, wanted)
        explanation += f"Answer '{answer}' on {question_id} sets grade {wanted}. "
    else:
        grade = nearest_grade(prices, calculated_price)
        explanation += (
            f"{best} grade price is {num(base_price)}. "
            f"Deductions add up to {num(raw_percent)}%. "
        )
        if cap_applied:
            explanation += f"The limit is {num(max_percent)}%, so {num(max_percent)}% was used. "
        explanation += (
            f"{num(base_price)} minus {num(total_percent)}% is {num(calculated_price)}. "
            f"The nearest grade price is {grade} grade, {num(prices[grade])}. "
        )

    final_price = prices[grade]

    if grade in borrowed:
        explanation += (
            f"This band has no {grade} grade price, so it was taken from "
            f"'{BAND_LABELS[borrowed[grade]]}'. "
        )

    explanation += f"The estimated price is {num(final_price)}."

    return {
        "grade": grade,
        "band": band,
        "band_label": BAND_LABELS[band],
        "in_warranty": bool(in_warranty),
        "age_months": age_months,
        "grade_prices": prices,
        "borrowed": borrowed,
        "forced": bool(forced),
        "base_price": base_price,
        "floor_price": floor_price,
        "total_percent": total_percent,
        "calculated_price": calculated_price,
        "final_price": final_price,
        "cap_applied": cap_applied,
        "floor_applied": calculated_price < floor_price,
        "explanation": explanation
    }


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


def erp_age_value(options, age_months):
    """
    The ERP value for the device age. With a dropdown such as
    '0-3 Months / 3-6 Months / 11+ Months' the matching option is returned;
    otherwise the number of months as text.
    """
    for option in options or []:
        numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", option)]
        text = option.lower()

        if len(numbers) >= 2 and numbers[0] <= age_months <= numbers[1]:
            return option

        if len(numbers) == 1:
            limit = numbers[0]
            more = "+" in option or ">" in option or any(w in text for w in ("above", "more", "over"))
            less = "<" in option or any(w in text for w in ("below", "less", "under", "up to", "upto"))

            if more and age_months >= limit:
                return option
            if less and age_months <= limit:
                return option
            if not more and not less and limit == age_months:
                return option

    return num(age_months)


# ---------------------------------------------------------------- the "Warranty" questions
# GetBuybackQuestionsByItem shows these two as a normal question category,
# so the app can ask them like every other question. They are not rows of
# the ERP Question Bank: their answers only choose the price band.
WARRANTY_CATEGORY = "Warranty"
WARRANTY_QUESTION = "WARRANTY_STATUS"
AGE_QUESTION = "DEVICE_AGE"

AGE_OPTIONS = (
    ("Up to 3 months", "0-3 months"),
    ("3 to 6 months", "3-6 months"),
    ("6 to 11 months", "6-11 months"),
    ("More than 11 months", "11+ months"),
)

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


def pricing_questions():
    """The two Warranty questions, in the same shape as the ERP questions."""
    def option(label, value):
        return {"OptionLabel": label, "OptionValue": value, "PriceImpactPercent": 0.0}

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
            "Options": [
                option(IN_WARRANTY_TEXT, IN_WARRANTY_TEXT),
                option(OUT_OF_WARRANTY_TEXT, OUT_OF_WARRANTY_TEXT),
            ]
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
            "Options": [option(label, value) for label, value in AGE_OPTIONS]
        }
    ]


def price_table(price_row):
    """The whole grade table of one phone, for showing to the app."""
    table = {}

    for band, label in BANDS:
        table[band] = {"label": label}
        for grade in GRADES:
            table[band][grade] = table_price(price_row or {}, grade, band)

    return table
