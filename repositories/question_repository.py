from core.database import get_db_connection
from pymysql.cursors import DictCursor


# =========================
# CUSTOMER QUESTIONS
# =========================
def get_buyback_question_list_repo():
    with get_db_connection() as conn:
        cursor = conn.cursor(DictCursor)

        cursor.execute("""
            SELECT 
                qb.name AS QuestionName,
                qb.question_text AS QuestionText,
                qb.question_type AS QuestionType,
                qb.question_category AS QuestionCategory,
                qb.display_order AS DisplayOrder,
                opt.option_label AS OptionLabel,
                opt.option_value AS OptionValue,
                opt.price_impact_percent AS PriceImpactPercent,
                opt.idx AS OptionOrder
            FROM `tabBuyback Question Bank` qb
            LEFT JOIN `tabBuyback Question Option` opt
                ON qb.name = opt.parent
            WHERE qb.diagnosis_type = 'Customer Question'
              AND qb.disabled = 0
            ORDER BY qb.display_order ASC, opt.idx ASC
        """)

        return cursor.fetchall()


# =========================
# AUTOMATED TESTS
# =========================
def get_automated_test_list_repo():
    with get_db_connection() as conn:
        cursor = conn.cursor(DictCursor)   # FIXED

        cursor.execute("""
            SELECT 
                qb.name AS QuestionName,
                qb.question_text AS QuestionText,
                qb.question_type AS QuestionType,
                qb.question_category AS QuestionCategory,
                qb.display_order AS DisplayOrder,   --  ADD THIS
                opt.option_label AS OptionLabel,
                opt.option_value AS OptionValue,
                opt.price_impact_percent AS PriceImpactPercent,
                opt.idx AS OptionOrder
            FROM `tabBuyback Question Bank` qb
            LEFT JOIN `tabBuyback Question Option` opt
                ON qb.name = opt.parent
            WHERE qb.diagnosis_type = 'Automated Test'
              AND qb.disabled = 0
            ORDER BY qb.display_order ASC, opt.idx ASC
        """)

        return cursor.fetchall()
# =========================================================
# MODEL BASED QUESTIONS CATEGORY WISE
# =========================================================
def get_buyback_questions_repo(item_code):

    with get_db_connection() as conn:

        cursor = conn.cursor(DictCursor)

        cursor.execute("""
            SELECT
                p.item_code,
                p.item_name,

                qb.name AS QuestionName,
                qb.question_text AS QuestionText,
                qb.question_type AS QuestionType,
                qb.question_category AS QuestionCategory,

                q.idx AS DisplayOrder,

                qb.question_code AS QuestionCode,

                opt.option_label AS OptionLabel,
                opt.option_value AS OptionValue,
                opt.price_impact_percent AS PriceImpactPercent,
                opt.idx AS OptionOrder

            FROM `tabBuyback Item Question Map` p

            INNER JOIN
            `tabBuyback Item Question Map Detail` q
                ON q.parent = p.name

            INNER JOIN
            `tabBuyback Question Bank` qb
                ON qb.name = q.question

            LEFT JOIN
            `tabBuyback Question Option` opt
                ON opt.parent = qb.name

            WHERE p.item_code = %s

            ORDER BY
                qb.question_category ASC,
                q.idx ASC,
                opt.idx ASC
        """, (item_code,))

        return cursor.fetchall()
# =========================================================
# GET MODEL BASED TESTS
# =========================================================
def get_buyback_tests_repo(item_code):

    with get_db_connection() as conn:

        cursor = conn.cursor(DictCursor)

        cursor.execute("""
            SELECT
                p.item_code AS ItemCode,
                p.item_name AS ItemName,

                t.idx AS DisplayOrder,

                t.test AS TestID,
                t.test_name AS TestName,
                t.test_code AS TestCode,

                qb.question_text AS TestText,
                qb.question_type AS TestType,
                qb.question_category AS TestCategory,

                opt.option_label AS OptionLabel,
                opt.option_value AS OptionValue,
                opt.price_impact_percent AS PriceImpactPercent,
                opt.idx AS OptionOrder

            FROM `tabBuyback Item Question Map` p

            INNER JOIN
            `tabBuyback Item Test Map Detail` t
                ON t.parent = p.name

            LEFT JOIN
            `tabBuyback Question Bank` qb
                ON qb.name = t.test

            LEFT JOIN
            `tabBuyback Question Option` opt
                ON opt.parent = qb.name

            WHERE p.item_code = %s
              AND qb.disabled = 0

            ORDER BY
                t.idx ASC,
                opt.idx ASC
        """, (item_code,))

        return cursor.fetchall()