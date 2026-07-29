from core.database import get_db_connection
from pymysql.cursors import DictCursor


# =========================================================
# GET THIRD PARTY BUYBACK QUESTIONS
# =========================================================
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


# =========================================================
# GET BASE PRICE
# =========================================================
def get_base_price_repo(item_code):

    with get_db_connection() as conn:

        cursor = conn.cursor(DictCursor)

        cursor.execute("""
            SELECT
                current_market_price,
                d_grade_oow_11
            FROM `tabBuyback Price Master`
            WHERE
                item_code = %s
                AND is_active = 1
            LIMIT 1
        """, (item_code,))

        return cursor.fetchone()


# =========================================================
# GET PRICE IMPACT %
# =========================================================
def get_price_percent_repo(question_id, answer_value):

    with get_db_connection() as conn:

        cursor = conn.cursor(DictCursor)

        cursor.execute("""
            SELECT
                price_impact_percent
            FROM `tabBuyback Question Option`
            WHERE
                parent = %s
                AND TRIM(LOWER(option_value)) =
                    TRIM(LOWER(%s))
            LIMIT 1
        """, (question_id, answer_value))

        row = cursor.fetchone()

        return float(row["price_impact_percent"]) if row else 0

# =========================================================
# GET FLOOR PRICE
def get_floor_price_repo(item_code):

    with get_db_connection() as conn:

        cursor = conn.cursor(DictCursor)

        cursor.execute("""
            SELECT
                d_grade_oow_11
            FROM `tabBuyback Price Master`
            WHERE
                item_code = %s
                AND is_active = 1
            LIMIT 1
        """, (item_code,))

        row = cursor.fetchone()

        return float(row["d_grade_oow_11"]) if row else 0
from datetime import datetime
from pymysql.cursors import DictCursor
import uuid

# =========================================================
# SAVE / UPDATE THIRD PARTY BUYBACK
# =========================================================
def create_thirdparty_buyback_repo(payload, estimated_price):

    with get_db_connection() as conn:

        cursor = conn.cursor(DictCursor)

        try:

            print("========================================")
            print("THIRD PARTY BUYBACK REQUEST")
            print(payload)
            print("Question Count :", len(payload.get("queAns", [])))
            print("========================================")

            # -------------------------------------------------
            # CHECK EXISTING ASSESSMENT
            # -------------------------------------------------
            cursor.execute("""
                SELECT name, assessment_id
                FROM `tabBuyback Assessment`
                WHERE imei_serial=%s
                AND mobile_no=%s
                ORDER BY creation DESC
                LIMIT 1
            """, (
                payload["imei_serial"],
                payload["mobile_no"]
            ))

            existing = cursor.fetchone()

            # =================================================
            # UPDATE
            # =================================================
            if existing:

                assessment_name = existing["name"]

                print("Updating Assessment :", assessment_name)

                cursor.execute("""
                    UPDATE `tabBuyback Assessment`
                    SET
                        modified=NOW(),
                        owner=%s,
                        source=%s,
                        company=%s,
                        item_group=%s,
                        customer=%s,
                        customer_name=%s,
                        mobile_no=%s,
                        ch_customer_id=%s,
                        item=%s,
                        item_name=%s,
                        brand=%s,
                        imei_serial=%s,
                        estimated_price=%s
                    WHERE name=%s
                """, (
                    payload.get("owner", "Administrator"),
                    payload.get("source"),
                    payload.get("company"),
                    payload.get("item_group"),
                    payload["customer"],
                    payload["customer_name"],
                    payload["mobile_no"],
                    payload.get("ch_customer_id"),
                    payload["item_code"],
                    payload["item_name"],
                    payload["brand"],
                    payload["imei_serial"],
                    estimated_price,
                    assessment_name
                ))

                cursor.execute("""
                    DELETE
                    FROM `tabBuyback Assessment Response`
                    WHERE parent=%s
                """, (assessment_name,))

            # =================================================
            # CREATE
            # =================================================
            else:

                year = datetime.now().strftime("%Y")

                cursor.execute("""
                    SELECT name
                    FROM `tabBuyback Assessment`
                    WHERE name LIKE %s
                    ORDER BY name DESC
                    LIMIT 1
                """, (f"BBA-{year}-%",))

                result = cursor.fetchone()

                number = (
                    int(result["name"].split("-")[-1]) + 1
                    if result else 1
                )

                assessment_name = f"BBA-{year}-{str(number).zfill(5)}"

                cursor.execute("""
                    SELECT MAX(assessment_id) max_id
                    FROM `tabBuyback Assessment`
                """)

                result = cursor.fetchone()

                assessment_id = (result["max_id"] or 0) + 1

                print("Creating Assessment :", assessment_name)

                cursor.execute("""
                    INSERT INTO `tabBuyback Assessment`
                    (
                        name,
                        assessment_id,
                        creation,
                        owner,
                        source,
                        company,
                        item_group,
                        customer,
                        customer_name,
                        mobile_no,
                        ch_customer_id,
                        item,
                        item_name,
                        brand,
                        imei_serial,
                        estimated_price,
                        status
                    )
                    VALUES
                    (
                        %s,%s,NOW(),%s,
                        %s,%s,%s,
                        %s,%s,%s,%s,
                        %s,%s,%s,%s,
                        %s,'Draft'
                    )
                """, (
                    assessment_name,
                    assessment_id,
                    payload.get("owner", "Administrator"),
                    payload.get("source"),
                    payload.get("company"),
                    payload.get("item_group"),
                    payload["customer"],
                    payload["customer_name"],
                    payload["mobile_no"],
                    payload.get("ch_customer_id"),
                    payload["item_code"],
                    payload["item_name"],
                    payload["brand"],
                    payload["imei_serial"],
                    estimated_price
                ))

            # =================================================
            # INSERT RESPONSES
            # =================================================

            print("========================================")
            print("INSERTING RESPONSES")
            print(payload.get("queAns", []))
            print("========================================")

            for idx, question in enumerate(payload.get("queAns", []), start=1):

                print(f"Question {idx} -> {question}")

                percent = get_price_percent_repo(
                    question["id"],
                    question["data"]
                )

                print("Percent :", percent)

                response_name = f"RESP-{uuid.uuid4().hex[:10]}"

                cursor.execute("""
                    INSERT INTO `tabBuyback Assessment Response`
                    (
                        name,
                        creation,
                        owner,
                        parent,
                        parentfield,
                        parenttype,
                        idx,
                        question_code,
                        answer_value,
                        price_impact_percent
                    )
                    VALUES
                    (
                        %s,
                        NOW(),
                        'Administrator',
                        %s,
                        'responses',
                        'Buyback Assessment',
                        %s,
                        %s,
                        %s,
                        %s
                    )
                """, (
                    response_name,
                    assessment_name,
                    idx,
                    question["id"],
                    question["data"],
                    percent
                ))

                print("Inserted :", response_name)

            conn.commit()

            print("SUCCESS")

            return {
                "assessment_name": assessment_name,
                "action": "Updated" if existing else "Created"
            }

        except Exception as e:

            conn.rollback()
            print("ERROR :", str(e))
            raise