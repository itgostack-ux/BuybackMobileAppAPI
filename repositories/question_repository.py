from core.database import get_db_connection


def get_buyback_question_list_repo():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT 
                    qb.name AS QuestionName,
                    qb.question_text AS QuestionText,
                    qb.question_type AS QuestionType,
                    opt.option_label AS OptionLabel,
                    opt.option_value AS OptionValue,
                    opt.price_impact_percent AS PriceImpactPercent
                FROM `tabBuyback Question Bank` qb
                LEFT JOIN `tabBuyback Question Option` opt
                    ON qb.name = opt.parent
                WHERE qb.disabled = 0
                ORDER BY qb.display_order, opt.idx
            """)

            return cursor.fetchall()

def get_automated_test_list_repo():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT 
                    qb.name AS QuestionName,
                    qb.question_text AS QuestionText,
                    qb.question_type AS QuestionType,
                    opt.option_label AS OptionLabel,
                    opt.option_value AS OptionValue,
                    opt.price_impact_percent AS PriceImpactPercent
                FROM `tabBuyback Question Bank` qb
                LEFT JOIN `tabBuyback Question Option` opt
                    ON qb.name = opt.parent
                WHERE qb.diagnosis_type = 'Automated Test'
                  AND qb.disabled = 0
                ORDER BY qb.display_order, opt.idx
            """)

            return cursor.fetchall()
            