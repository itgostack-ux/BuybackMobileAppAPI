from core.database import get_db_connection


def _get_table_columns(cursor, table_name):
    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = %s
    """, (table_name,))

    return {row["column_name"] for row in cursor.fetchall()}


def _first_existing_column(columns, candidates):
    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


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


def get_buyback_price_item_repo(item_code):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    bpm.item_code,
                    bpm.item_name,
                    i.ch_item_group_id,
                    i.ch_brand_id,
                    i.ch_model_id,
                    m.category_id,
                    m.item_group_id,
                    m.brand_id,
                    m.brand,
                    CASE
                        WHEN LOWER(IFNULL(m.brand, '')) LIKE '%%apple%%' THEN 'iOS'
                        ELSE 'Android'
                    END AS platform
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


def get_buyback_questions_by_item_repo(item_code):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    qb.question_category AS QuestionCategory,
                    qb.diagnosis_type AS DiagnosisType,
                    qb.question_id AS QuestionID,
                    qb.name AS QuestionName,
                    qb.question_text AS QuestionText,
                    qb.question_code AS QuestionCode,
                    qb.question_type AS QuestionType,
                    qb.is_mandatory AS Mandatory,
                    qb.disabled AS Disabled,
                    opt.option_label AS OptionLabel,
                    opt.option_value AS OptionValue,
                    opt.price_impact_percent AS PriceImpactPercent
                FROM `tabBuyback Item Question Map` bqm
                JOIN `tabBuyback Item Question Map Detail` bqmd
                    ON bqmd.parent = bqm.name
                JOIN `tabBuyback Question Bank` qb
                    ON qb.name = bqmd.question
                JOIN `tabBuyback Price Master` bpm
                    ON bpm.item_code = bqm.item_code
                    AND bpm.is_active = 1
                LEFT JOIN `tabBuyback Question Option` opt
                    ON qb.name = opt.parent
                WHERE bqm.item_code = %s
                  AND qb.disabled = 0
                  AND IFNULL(qb.diagnosis_type, '') != 'Automated Test'
                ORDER BY bqmd.idx, qb.display_order, qb.question_id, opt.idx
            """, (item_code,))

            return cursor.fetchall()


def get_buyback_questions_by_item_mapping_fallback_repo(item_code):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    qb.question_category AS QuestionCategory,
                    qb.diagnosis_type AS DiagnosisType,
                    qb.question_id AS QuestionID,
                    qb.name AS QuestionName,
                    qb.question_text AS QuestionText,
                    qb.question_code AS QuestionCode,
                    qb.question_type AS QuestionType,
                    qb.is_mandatory AS Mandatory,
                    qb.disabled AS Disabled,
                    opt.option_label AS OptionLabel,
                    opt.option_value AS OptionValue,
                    opt.price_impact_percent AS PriceImpactPercent
                FROM `tabBuyback Question Bank` qb
                LEFT JOIN `tabBuyback Question Option` opt
                    ON qb.name = opt.parent
                JOIN `tabBuyback Price Master` bpm
                    ON bpm.item_code = %s
                    AND bpm.is_active = 1
                LEFT JOIN `tabItem` i
                    ON i.item_code = bpm.item_code
                LEFT JOIN `tabCH Model` m
                    ON m.model_id = i.ch_model_id
                WHERE qb.disabled = 0
                  AND IFNULL(qb.diagnosis_type, '') != 'Automated Test'
                  AND (
                      qb.applies_to_category IS NULL
                      OR TRIM(qb.applies_to_category) = ''
                      OR LOWER(TRIM(qb.applies_to_category)) = 'any'
                      OR CAST(qb.applies_to_category AS UNSIGNED) = i.ch_item_group_id
                      OR CAST(qb.applies_to_category AS UNSIGNED) = m.item_group_id
                      OR CAST(qb.applies_to_category AS UNSIGNED) = m.category_id
                  )
                  AND (
                      qb.applies_to_brand_family IS NULL
                      OR TRIM(qb.applies_to_brand_family) = ''
                      OR LOWER(TRIM(qb.applies_to_brand_family)) = 'any'
                      OR (
                          LOWER(IFNULL(m.brand, '')) LIKE '%%apple%%'
                          AND LOWER(TRIM(qb.applies_to_brand_family)) IN ('apple', 'ios')
                      )
                      OR (
                          LOWER(IFNULL(m.brand, '')) NOT LIKE '%%apple%%'
                          AND LOWER(TRIM(qb.applies_to_brand_family)) = 'android'
                      )
                  )
                ORDER BY qb.display_order, qb.question_id, opt.idx
            """, (item_code,))

            return cursor.fetchall()


def get_diagnostic_questions_by_platform_repo(brand_families):
    placeholders = ",".join(["%s"] * len(brand_families))

    with get_db_connection() as conn:
        with conn.cursor() as cursor:

            cursor.execute(f"""
                SELECT
                    qb.question_category AS QuestionCategory,
                    qb.diagnosis_type AS DiagnosisType,
                    qb.question_id AS QuestionID,
                    qb.name AS QuestionName,
                    qb.question_text AS QuestionText,
                    qb.question_code AS QuestionCode,
                    qb.question_type AS QuestionType,
                    qb.is_mandatory AS Mandatory,
                    qb.disabled AS Disabled,
                    qb.applies_to_brand_family AS AppliesToBrandFamily,
                    opt.option_label AS OptionLabel,
                    opt.option_value AS OptionValue,
                    opt.price_impact_percent AS PriceImpactPercent
                FROM `tabBuyback Question Bank` qb
                LEFT JOIN `tabBuyback Question Option` opt
                    ON qb.name = opt.parent
                WHERE qb.disabled = 0
                  AND qb.diagnosis_type = 'Automated Test'
                  AND (
                      qb.applies_to_brand_family IS NULL
                      OR qb.applies_to_brand_family = ''
                      OR qb.applies_to_brand_family IN ({placeholders})
                  )
                ORDER BY qb.display_order, qb.question_id, opt.idx
            """, tuple(brand_families))

            return cursor.fetchall()
            
