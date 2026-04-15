# repositories/buyback_repository.py

from core.database import get_db_connection
from pymysql.cursors import DictCursor
from datetime import datetime
import uuid


class BuybackRepository:

    # ✅ GET BUYBACK PRICE
    def fetch_buyback_price(self, item_code=None, buyback_price_id=None):

        query = """
            SELECT
                buyback_price_id,
                sku_id,
                item_code,
                item_name,
                current_market_price,
                vendor_price,
                is_active
            FROM `tabBuyback Price Master`
            WHERE is_active = 1
        """

        params = []

        if item_code:
            query += " AND item_code = %s"
            params.append(item_code)

        if buyback_price_id:
            query += " AND buyback_price_id = %s"
            params.append(buyback_price_id)

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)
            cursor.execute(query, params)
            return cursor.fetchone()


    # ✅ BASE PRICE
    def get_base_price(self, item_code):

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT current_market_price
                FROM `tabBuyback Price Master`
                WHERE item_code = %s AND is_active = 1
                LIMIT 1
            """, (item_code,))

            return cursor.fetchone()


    # ✅ QUESTION DETAILS (FIXED)
    def get_question_details(self, question_code):

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT 
                    name,
                    question_id,
                    question_code,
                    question_text,
                    idx
                FROM `tabBuyback Question Bank`
                WHERE name = %s
                LIMIT 1
            """, (question_code,))

            return cursor.fetchone()


    # ✅ PRICE %
    def get_price_percent(self, question_code, answer_value):

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT price_impact_percent
                FROM `tabBuyback Question Option`
                WHERE parent = %s
                  AND TRIM(LOWER(option_value)) = TRIM(LOWER(%s))
                LIMIT 1
            """, (question_code, answer_value))

            result = cursor.fetchone()
            return float(result["price_impact_percent"]) if result else 0


    # ✅ NAME GENERATION
    def generate_assessment_name(self):

        year = datetime.now().strftime("%Y")

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT name
                FROM `tabBuyback Assessment`
                WHERE name LIKE %s
                ORDER BY name DESC
                LIMIT 1
            """, (f"BBA-{year}-%",))

            result = cursor.fetchone()

            if result:
                last_number = int(result["name"].split("-")[-1])
                new_number = last_number + 1
            else:
                new_number = 1

        return f"BBA-{year}-{str(new_number).zfill(5)}"


    # ✅ assessment_id
    def generate_assessment_id(self):

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT MAX(assessment_id) AS max_id
                FROM `tabBuyback Assessment`
            """)

            result = cursor.fetchone()
            return (result["max_id"] or 0) + 1


    # ✅ CREATE ASSESSMENT
    def create_assessment(self, payload, estimated_price):

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            try:
                name = self.generate_assessment_name()
                assessment_id = self.generate_assessment_id()

                cursor.execute("""
                    INSERT INTO `tabBuyback Assessment` (
                        name,
                        assessment_id,
                        creation,
                        owner,
                        source,
                        customer,
                        customer_name,
                        mobile_no,
                        company,
                        item_group,
                        item,
                        item_name,
                        brand,
                        imei_serial,
                        estimated_price,
                        status
                    )
                    VALUES (%s,%s,NOW(),%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s,%s,'Draft')
                """, (
                    name,
                    assessment_id,
                    payload.get("owner", "Administrator"),
                    payload.get("source", "Mobile App"),
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

                for idx, r in enumerate(payload.get("responses", []), start=1):

                    q = self.get_question_details(r["question_code"])
                    child_name = f"RESP-{uuid.uuid4().hex[:10]}"

                    cursor.execute("""
                        INSERT INTO `tabBuyback Assessment Response` (
                            name,
                            creation,
                            owner,
                            parent,
                            parenttype,
                            parentfield,
                            idx,
                            question_code,
                            question_text,
                            answer_value,
                            answer_label,
                            price_impact_percent
                        )
                        VALUES (%s,NOW(),%s,%s,
                                'Buyback Assessment','responses',
                                %s,%s,%s,%s,%s,%s)
                    """, (
                        child_name,
                        payload.get("owner", "Administrator"),
                        name,
                        idx,
                        r["question_code"],
                        q["question_text"] if q else "",
                        r["answer_value"],
                        r["answer_value"],
                        0
                    ))

                conn.commit()
                return name

            except Exception as e:
                conn.rollback()
                raise e