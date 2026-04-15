from core.database import get_db_connection
from pymysql.cursors import DictCursor
from datetime import datetime
import uuid


class BuybackRepository:

    # =========================
    # 1️⃣ FETCH BUYBACK PRICE (ONLY ITEM CODE)
    # =========================
    def fetch_buyback_price(self, item_code):

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT
                    name AS buyback_price_id,
                    item_code,
                    item_name,
                    current_market_price,
                    vendor_price,
                    is_active
                FROM `tabBuyback Price Master`
                WHERE item_code = %s
                AND is_active = 1
                LIMIT 1
            """, (item_code,))

            return cursor.fetchone()

    # =========================
    # 2️⃣ BASE PRICE
    # =========================
    def get_base_price(self, item_code):

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT current_market_price, d_grade_oow_11
                FROM `tabBuyback Price Master`
                WHERE item_code = %s
                AND is_active = 1
                LIMIT 1
            """, (item_code,))

            return cursor.fetchone()

    # =========================
    # 3️⃣ FLOOR PRICE
    # =========================
    def get_floor_price(self, item_code):

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT d_grade_oow_11
                FROM `tabBuyback Price Master`
                WHERE item_code = %s
                AND is_active = 1
                LIMIT 1
            """, (item_code,))

            result = cursor.fetchone()
            return float(result["d_grade_oow_11"]) if result else 0

    # =========================
    # 4️⃣ PRICE IMPACT %
    # =========================
    def get_price_percent(self, question_id, answer_value):

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT price_impact_percent
                FROM `tabBuyback Question Option`
                WHERE parent = %s
                  AND TRIM(LOWER(option_value)) = TRIM(LOWER(%s))
                LIMIT 1
            """, (question_id, answer_value))

            result = cursor.fetchone()
            return float(result["price_impact_percent"]) if result else 0

    # =========================
    # 5️⃣ QUESTION DETAILS
    # =========================
    def get_question_details(self, question_id):

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT name, question_text
                FROM `tabBuyback Question Bank`
                WHERE name = %s
                LIMIT 1
            """, (question_id,))

            return cursor.fetchone()

    # =========================
    # 6️⃣ GENERATE NAME
    # =========================
    def generate_assessment_name(self):

        year = datetime.now().strftime("%Y")

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT name FROM `tabBuyback Assessment`
                WHERE name LIKE %s
                ORDER BY name DESC LIMIT 1
            """, (f"BBA-{year}-%",))

            result = cursor.fetchone()
            number = int(result["name"].split("-")[-1]) + 1 if result else 1

        return f"BBA-{year}-{str(number).zfill(5)}"

    # =========================
    # 7️⃣ GENERATE ID
    # =========================
    def generate_assessment_id(self):

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT MAX(assessment_id) AS max_id
                FROM `tabBuyback Assessment`
            """)

            result = cursor.fetchone()
            return (result["max_id"] or 0) + 1

    # =========================
    # 8️⃣ CREATE ASSESSMENT
    # =========================
    def create_assessment(self, payload, estimated_price):

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            name = self.generate_assessment_name()
            assessment_id = self.generate_assessment_id()

            cursor.execute("""
                INSERT INTO `tabBuyback Assessment`
                (name, assessment_id, creation, owner, source,
                 customer, customer_name, mobile_no,
                 company, item_group, item, item_name,
                 brand, imei_serial, estimated_price, status)
                VALUES (%s,%s,NOW(),%s,%s,%s,%s,%s,
                        %s,%s,%s,%s,%s,%s,%s,'Draft')
            """, (
                name,
                assessment_id,
                payload.get("owner", "Administrator"),
                payload.get("source", "Web"),
                payload["customer"],
                payload["customer_name"],
                payload["mobile_no"],
                payload.get("company", ""),
                payload.get("item_group", ""),
                payload["item_code"],
                payload["item_name"],
                payload["brand"],
                payload["imei_serial"],
                estimated_price
            ))

            # OPTIONAL: save responses
            for idx, r in enumerate(payload.get("responses", []), start=1):

                q = self.get_question_details(r["question_id"])
                percent = self.get_price_percent(r["question_id"], r["answer_value"])

                cursor.execute("""
                    INSERT INTO `tabBuyback Assessment Response`
                    (name, creation, owner, parent, parenttype, parentfield,
                     idx, question_code, question_text,
                     answer_value, answer_label, price_impact_percent)
                    VALUES (%s,NOW(),%s,%s,'Buyback Assessment','responses',
                            %s,%s,%s,%s,%s,%s)
                """, (
                    f"RESP-{uuid.uuid4().hex[:10]}",
                    payload.get("owner", "Administrator"),
                    name,
                    idx,
                    r["question_id"],
                    q["question_text"] if q else "",
                    r["answer_value"],
                    r["answer_value"],
                    percent
                ))

            conn.commit()
            return name