from core.database import get_db_connection

SMARTPHONE_CATEGORY_ID = 3

def fetch_query(query, params=None):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or [])
            return cursor.fetchall()


def get_brands_by_subcategory_repo(item_group_id=None):
    query = """
        SELECT DISTINCT
            brand_id,
            brand
        FROM `tabCH Model`
        WHERE IFNULL(disabled,0)=0
          AND category_id=%s
    """
 
    params = [SMARTPHONE_CATEGORY_ID]
 
    if item_group_id:
        query += " AND item_group_id=%s"
        params.append(item_group_id)
 
    query += " ORDER BY brand"
 
    return fetch_query(query, params)

def get_models_filtered_repo(
    item_group_id=None,
    brand_id=None
):
    query = """
        SELECT
            name,
            model_id,
            model_name,
            brand_id
        FROM `tabCH Model`
        WHERE IFNULL(disabled,0)=0
    """

    params = []

    if item_group_id:
        query += " AND item_group_id=%s"
        params.append(item_group_id)


    if brand_id:
        query += " AND brand_id=%s"
        params.append(brand_id)

    query += " ORDER BY model_name"

    return fetch_query(query, params)


def get_attribute_values_repo(model_id):
    return fetch_query("""
        SELECT DISTINCT
            ram.attribute_value AS ram,
            storage.attribute_value AS storage
        FROM `tabItem` i
        LEFT JOIN `tabItem Variant Attribute` ram
            ON ram.parent = i.name AND ram.attribute = 'RAM'
        JOIN `tabItem Variant Attribute` storage
            ON storage.parent = i.name AND storage.attribute = 'Storage'
        WHERE i.disabled = 0
            AND i.ch_model_id = %s
        ORDER BY ram.attribute_value, storage.attribute_value
        """, (model_id,))

def get_items_repo(
    item_group_id,
    brand_id,
    model_id,
    filters: dict
):
    conditions = []
    params = [
        item_group_id,
        brand_id,
        model_id
    ]

    

    for attr, value in filters.items():
        conditions.append("(a.attribute=%s AND a.attribute_value=%s)")
        params.extend([attr, value])

    query = f"""
        SELECT
            i.item_code,
            i.item_name
        FROM `tabItem` i
        JOIN `tabItem Variant Attribute` a
            ON a.parent = i.name
        WHERE
            i.disabled = 0
            AND i.ch_item_group_id = %s
            AND i.ch_brand_id = %s
            AND i.ch_model_id = %s
            AND ({' OR '.join(conditions)})
        GROUP BY i.name, i.item_code, i.item_name
        HAVING COUNT(DISTINCT a.attribute) = %s
    """

    params.append(len(filters))

    return fetch_query(query, tuple(params))


def get_colors_by_storage_repo(model_id: int, storage_value: str, ram_value: str | None = None):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                SELECT DISTINCT
                    color.spec_value AS color
                FROM `tabCH Model Spec Value` storage
                JOIN `tabCH Model Spec Value` color
                    ON color.parent = storage.parent
                JOIN `tabCH Model` m
                    ON m.name = storage.parent
                """
                params = []

                if ram_value:
                    query += """
                JOIN `tabCH Model Spec Value` ram
                    ON ram.parent = storage.parent
                    AND ram.spec = 'RAM'
                    AND ram.spec_value = %s
                """
                    params.append(ram_value)

                query += """
                WHERE m.model_id = %s
                    AND storage.spec = 'Storage'
                    AND storage.spec_value = %s
                    AND color.spec = 'Colour'
                ORDER BY color.spec_value
                """
                params.extend([model_id, storage_value])

                cursor.execute(query, tuple(params))

                return cursor.fetchall()

    except Exception as e:
        raise Exception(f"Repo Error: {str(e)}")

def get_buyback_price_repo(item_code):
    return fetch_query("""
        SELECT 
            name,
            sku_id,
            buyback_price_id,
            item_code,
            item_name,
            current_market_price,
            vendor_price,
            a_grade_iw_0_3,
            b_grade_iw_0_3,
            c_grade_iw_0_3,
            a_grade_iw_0_6,
            b_grade_iw_0_6,
            c_grade_iw_0_6,
            d_grade_iw_0_6,
            a_grade_iw_6_11,
            b_grade_iw_6_11,
            c_grade_iw_6_11,
            d_grade_iw_6_11,
            a_grade_oow_11,
            b_grade_oow_11,
            c_grade_oow_11,
            d_grade_oow_11,
            scrap_price,
            phone_dead_price
        FROM `tabBuyback Price Master`
        WHERE item_code = %s
    """, (item_code,))