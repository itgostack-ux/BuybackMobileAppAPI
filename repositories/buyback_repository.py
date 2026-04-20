from core.database import get_db_connection
from pymysql.cursors import DictCursor
from datetime import datetime
import uuid


class BuybackRepository:

    # =========================
    # BASE PRICE
    # =========================
    def get_base_price(self, item_code):
        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT current_market_price, d_grade_oow_11
                FROM `tabBuyback Price Master`
                WHERE item_code = %s AND is_active = 1
                LIMIT 1
            """, (item_code,))

            return cursor.fetchone()

    # =========================
    # FLOOR PRICE
    # =========================
    def get_floor_price(self, item_code):
        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT d_grade_oow_11
                FROM `tabBuyback Price Master`
                WHERE item_code = %s AND is_active = 1
                LIMIT 1
            """, (item_code,))

            result = cursor.fetchone()
            return float(result["d_grade_oow_11"]) if result else 0

    # =========================
    # COMMON % (RESP + DIAG)
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
    # GENERATE NAME
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
    # CREATE BASIC (RESP ONLY)
    # =========================
    def create_assessment(self, payload, estimated_price):

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            name = self.generate_assessment_name()
            assessment_id = self.generate_assessment_id()

            # MAIN
            cursor.execute("""
                INSERT INTO `tabBuyback Assessment`
                (name, assessment_id, creation, owner,
                 customer, customer_name, mobile_no,
                 item, item_name, brand, imei_serial,
                 estimated_price, status)
                VALUES (%s,%s,NOW(),'Administrator',
                        %s,%s,%s,%s,%s,%s,%s,%s,'Draft')
            """, (
                name, assessment_id,
                payload["customer"],
                payload["customer_name"],
                payload["mobile_no"],
                payload["item_code"],
                payload["item_name"],
                payload["brand"],
                payload["imei_serial"],
                estimated_price
            ))

            # RESPONSES
            for idx, r in enumerate(payload.get("responses", []), start=1):

                percent = self.get_price_percent(r["question_id"], r["answer_value"])

                cursor.execute("""
                    INSERT INTO `tabBuyback Assessment Response`
                    (name, creation, owner, parent, parenttype, parentfield,
                     idx, question_code,
                     answer_value, price_impact_percent)
                    VALUES (%s,NOW(),'Administrator',%s,'Buyback Assessment','responses',
                            %s,%s,%s,%s)
                """, (
                    f"RESP-{uuid.uuid4().hex[:10]}",
                    name,
                    idx,
                    r["question_id"],
                    r["answer_value"],
                    percent
                ))

            conn.commit()
            return name

    # =========================
    # CREATE FULL (RESP + DIAG)
    # =========================
    def create_full_assessment(self, payload, estimated_price):

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            name = self.generate_assessment_name()
            assessment_id = self.generate_assessment_id()

            # MAIN
            cursor.execute("""
                INSERT INTO `tabBuyback Assessment`
                (name, assessment_id, creation, owner,
                 customer, customer_name, mobile_no,
                 item, item_name, brand, imei_serial,
                 estimated_price, status)
                VALUES (%s,%s,NOW(),'Administrator',
                        %s,%s,%s,%s,%s,%s,%s,%s,'Draft')
            """, (
                name, assessment_id,
                payload["customer"],
                payload["customer_name"],
                payload["mobile_no"],
                payload["item_code"],
                payload["item_name"],
                payload["brand"],
                payload["imei_serial"],
                estimated_price
            ))

            # RESPONSES
            for idx, r in enumerate(payload.get("responses", []), start=1):

                percent = self.get_price_percent(r["question_id"], r["answer_value"])

                cursor.execute("""
                    INSERT INTO `tabBuyback Assessment Response`
                    (name, creation, owner, parent, parenttype, parentfield,
                     idx, question_code,
                     answer_value, price_impact_percent)
                    VALUES (%s,NOW(),'Administrator',%s,'Buyback Assessment','responses',
                            %s,%s,%s,%s)
                """, (
                    f"RESP-{uuid.uuid4().hex[:10]}",
                    name,
                    idx,
                    r["question_id"],
                    r["answer_value"],
                    percent
                ))

            # =========================
            # DIAGNOSTICS (FIXED)
            # =========================
            for idx, d in enumerate(payload.get("diagnostics", []), start=1):

                percent = self.get_price_percent(
                    d["test_code"],
                    d["result"]
                )

                cursor.execute("""
                    INSERT INTO `tabBuyback Assessment Diagnostic`
                    (name, creation, owner, parent, parenttype, parentfield,
                     idx, test, test_code, test_name, result, depreciation_percent)
                    VALUES (%s, NOW(), 'Administrator', %s, 'Buyback Assessment', 'diagnostic_tests',
                            %s, %s, %s, %s, %s, %s)
                """, (
                    f"DIAG-{uuid.uuid4().hex[:10]}",
                    name,
                    idx,
                    d["test_code"],   # REQUIRED FIELD
                    d["test_code"],
                    d["test_name"],
                    d["result"],
                    percent
                ))

            conn.commit()
            return name