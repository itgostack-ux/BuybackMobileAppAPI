from core.database import get_db_connection


def get_questions_repo():

    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    question_id AS QuestionID,
                    question_text AS QuestionText,
                    question_description AS QuestionDescription,
                    question_type AS QuestionType
                FROM `tabQuestion Master`
                WHERE is_active = 1
                ORDER BY question_id
            """)

            questions = cursor.fetchall()

            if not questions:
                return [], []

            question_ids = [str(q["QuestionID"]) for q in questions]

            format_strings = ",".join(["%s"] * len(question_ids))

            cursor.execute(f"""
                SELECT
                    question_id AS QuestionID,
                    option_id AS OptionID,
                    option_text AS OptionText,
                    grade_id AS GradeID,
                    grade_name AS GradeName
                FROM `tabOption Master`
                WHERE is_active = 1
                AND question_id IN ({format_strings})
                ORDER BY question_id, option_id
            """, tuple(question_ids))

            options = cursor.fetchall()

    return questions, options