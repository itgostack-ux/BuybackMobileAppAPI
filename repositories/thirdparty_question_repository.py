from core.database import get_db_connection
from pymysql.cursors import DictCursor


def get_thirdparty_buyback_questions_repo(item_code):

    with get_db_connection() as conn:

        cursor = conn.cursor(DictCursor)

        cursor.execute("""
            SELECT
                p.item_code AS ProductId,

                qb.name AS QuestionId,
                qb.question_text,

                opt.idx,
                opt.option_label,
                opt.option_value

            FROM `tabBuyback Item Question Map` p

            INNER JOIN `tabBuyback Item Question Map Detail` d
                ON d.parent = p.name

            INNER JOIN `tabBuyback Question Bank` qb
                ON qb.name = d.question

            LEFT JOIN `tabBuyback Question Option` opt
                ON opt.parent = qb.name

            WHERE
                p.item_code = %s
                AND qb.disabled = 0

            ORDER BY
                d.idx,
                opt.idx
        """, (item_code,))

        return cursor.fetchall()