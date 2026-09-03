from core.database import get_db_connection
from pymysql.cursors import DictCursor
from datetime import datetime
import uuid


class BuybackRepository:
    def get_table_columns(self, table_name):
        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                  AND table_name = %s
            """, (table_name,))

            return {row["column_name"] for row in cursor.fetchall()}

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

    def get_item_for_assessment(self, item_code):
        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT
                    bpm.item_code,
                    bpm.item_name,
                    bpm.current_market_price,
                    bpm.d_grade_oow_11,
                    i.ch_item_group_id AS item_group,
                    m.brand
                FROM `tabBuyback Price Master` bpm
                LEFT JOIN `tabItem` i
                    ON i.item_code = bpm.item_code
                LEFT JOIN `tabCH Model` m
                    ON m.model_id = i.ch_model_id
                WHERE bpm.item_code = %s
                  AND bpm.is_active = 1
                LIMIT 1
            """, (item_code,))

            return cursor.fetchone()

    def get_customer_for_assessment(self, customer_id):
        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT name, customer_name, mobile_no
                FROM `tabCustomer`
                WHERE name = %s
                   OR mobile_no = %s
                LIMIT 1
            """, (customer_id, customer_id))

            return cursor.fetchone()

    def get_mapped_question_for_item(self, item_code, question_name=None, question_code=None):
        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT
                    qb.name,
                    qb.question_code,
                    qb.question_text
                FROM `tabBuyback Item Question Map` bqm
                JOIN `tabBuyback Item Question Map Detail` bqmd
                    ON bqmd.parent = bqm.name
                JOIN `tabBuyback Question Bank` qb
                    ON qb.name = bqmd.question
                WHERE bqm.item_code = %s
                  AND IFNULL(qb.diagnosis_type, '') != 'Automated Test'
                  AND (
                      (%s IS NOT NULL AND qb.name = %s)
                      OR (%s IS NOT NULL AND qb.question_code = %s)
                  )
                LIMIT 1
            """, (
                item_code,
                question_name,
                question_name,
                question_code,
                question_code
            ))

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

    def get_assessment_for_sell_now(self, assessment_name):
        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT
                    name,
                    customer,
                    customer_name,
                    mobile_no,
                    store,
                    company,
                    item,
                    item_group,
                    brand,
                    item_name,
                    imei_serial,
                    estimated_grade,
                    warranty_status,
                    estimated_price,
                    quoted_price,
                    status
                FROM `tabBuyback Assessment`
                WHERE name = %s
                LIMIT 1
            """, (assessment_name,))

            return cursor.fetchone()

    def get_order_by_assessment(self, assessment_name):
        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT
                    name,
                    order_id,
                    buyback_assessment,
                    customer,
                    item,
                    final_price,
                    approved_price,
                    status,
                    workflow_state
                FROM `tabBuyback Order`
                WHERE buyback_assessment = %s
                ORDER BY creation DESC
                LIMIT 1
            """, (assessment_name,))

            return cursor.fetchone()

    def generate_order_name(self):
        year = datetime.now().strftime("%Y")

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT name FROM `tabBuyback Order`
                WHERE name LIKE %s
                ORDER BY name DESC LIMIT 1
            """, (f"BBO-{year}-%",))

            result = cursor.fetchone()
            number = int(result["name"].split("-")[-1]) + 1 if result else 1

        return f"BBO-{year}-{str(number).zfill(5)}"

    def generate_order_id(self):
        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute("""
                SELECT MAX(order_id) AS max_id
                FROM `tabBuyback Order`
            """)

            result = cursor.fetchone()
            return (result["max_id"] or 0) + 1

    def create_sell_now_order(self, payload, assessment):
        order_name = self.generate_order_name()
        order_id = self.generate_order_id()
        columns = self.get_table_columns("tabBuyback Order")

        row = {
            "name": order_name,
            "order_id": order_id,
            "creation": "NOW()",
            "modified": "NOW()",
            "owner": "Administrator",
            "modified_by": "Administrator",
            "buyback_assessment": assessment["name"],
            "settlement_type": payload.get("settlement_type") or "Cash",
            "customer": assessment.get("customer"),
            "customer_name": assessment.get("customer_name"),
            "mobile_no": assessment.get("mobile_no"),
            "store": payload.get("store") or assessment.get("store"),
            "company": payload.get("company") or assessment.get("company"),
            "status": "Draft",
            "workflow_state": "Draft",
            "item": assessment.get("item"),
            "item_name": assessment.get("item_name"),
            "item_group": assessment.get("item_group"),
            "brand": assessment.get("brand"),
            "imei_serial": assessment.get("imei_serial"),
            "condition_grade": assessment.get("estimated_grade"),
            "warranty_status": assessment.get("warranty_status"),
            "base_price": assessment.get("quoted_price") or assessment.get("estimated_price"),
            "total_deductions": 0,
            "final_price": assessment.get("estimated_price"),
            "approved_price": assessment.get("estimated_price"),
            "payment_status": "Pending",
            "customer_payout_mode": payload.get("customer_payout_mode"),
            "remarks": payload.get("remarks")
        }

        insert_columns = [column for column in row if column in columns]
        values = []
        placeholders = []

        for column in insert_columns:
            if row[column] == "NOW()":
                placeholders.append("NOW()")
            else:
                placeholders.append("%s")
                values.append(row[column])

        column_sql = ", ".join(f"`{column}`" for column in insert_columns)
        placeholder_sql = ", ".join(placeholders)

        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            cursor.execute(f"""
                INSERT INTO `tabBuyback Order`
                ({column_sql})
                VALUES ({placeholder_sql})
            """, tuple(values))

            cursor.execute("""
                UPDATE `tabBuyback Assessment`
                SET status = 'Submitted',
                    modified = NOW(),
                    modified_by = 'Administrator'
                WHERE name = %s
            """, (assessment["name"],))

            conn.commit()

        return order_name

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

    def create_mobile_answer_assessment(self, payload, customer, item, answers, estimated_price):
        with get_db_connection() as conn:
            cursor = conn.cursor(DictCursor)

            name = self.generate_assessment_name()
            assessment_id = self.generate_assessment_id()

            cursor.execute("""
                INSERT INTO `tabBuyback Assessment`
                (name, assessment_id, creation, modified, owner, modified_by,
                 customer, customer_name, mobile_no,
                 item, item_name, brand, imei_serial,
                 source, estimated_price, status)
                VALUES (%s,%s,NOW(),NOW(),'Administrator','Administrator',
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,'Draft')
            """, (
                name,
                assessment_id,
                customer["name"],
                customer["customer_name"],
                customer["mobile_no"],
                item["item_code"],
                item["item_name"],
                item.get("brand"),
                payload["imei_serial"],
                payload.get("source") or "Mobile App",
                estimated_price
            ))

            for idx, answer in enumerate(answers, start=1):
                cursor.execute("""
                    INSERT INTO `tabBuyback Assessment Response`
                    (name, creation, modified, owner, modified_by,
                     parent, parenttype, parentfield, idx,
                     question, question_code, question_text,
                     answer_value, answer_label, price_impact_percent)
                    VALUES (%s,NOW(),NOW(),'Administrator','Administrator',
                            %s,'Buyback Assessment','responses',%s,
                            %s,%s,%s,%s,%s,%s)
                """, (
                    f"RESP-{uuid.uuid4().hex[:10]}",
                    name,
                    idx,
                    answer["question_name"],
                    answer["question_code"],
                    answer["question_text"],
                    answer["answer_value"],
                    answer["answer_value"],
                    answer["price_impact_percent"]
                ))

            conn.commit()
            return name
