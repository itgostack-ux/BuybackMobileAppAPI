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
                qb.display_order AS DisplayOrder,   -- ✅ ADD THIS
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