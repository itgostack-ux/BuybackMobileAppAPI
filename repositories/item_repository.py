from core.database import get_db_connection


def fetch_query(query, params=None):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or [])
            return cursor.fetchall()


def get_device_items_repo():
    return fetch_query("""
        SELECT name,item_group_id,item_group_name,parent_item_group,is_group,lft,rgt
        FROM `tabItem Group`
        WHERE IFNULL(ch_disabled,0)=0
        AND IFNULL(ch_is_active,0)=1
        ORDER BY lft
    """)


def get_categories_repo(item_group_id):
    return fetch_query("""
        SELECT name,category_id,category_name,item_group_id
        FROM `tabCH Category`
        WHERE IFNULL(disabled,0)=0
        AND item_group_id=%s
        ORDER BY category_id
    """,(item_group_id,))


def get_sub_categories_repo(category_id=None,item_group_id=None):

    query="""
        SELECT name,sub_category_id,sub_category_name,
        category_id,item_group_id
        FROM `tabCH Sub Category`
        WHERE IFNULL(disabled,0)=0
    """

    params=[]

    if category_id:
        query+=" AND category_id=%s"
        params.append(category_id)

    if item_group_id:
        query+=" AND item_group_id=%s"
        params.append(item_group_id)

    return fetch_query(query,params)








def get_brands_by_subcategory_repo(item_group_id=None, category_id=None, sub_category_id=None):
    query = """
        SELECT DISTINCT
            brand_id,
            brand
        FROM `tabCH Model`
        WHERE IFNULL(disabled,0)=0
    """

    params = []

    if item_group_id:
        query += " AND item_group_id=%s"
        params.append(item_group_id)

    if category_id:
        query += " AND category_id=%s"
        params.append(category_id)

    if sub_category_id:
        query += " AND sub_category_id=%s"
        params.append(sub_category_id)

    query += " ORDER BY brand"

    return fetch_query(query, params)








def get_model_with_spec_repo(model_id=None):

    query="""
        SELECT m.model_id,m.model_name,m.brand,
        s.spec,s.spec_value
        FROM `tabCH Model` m
        JOIN `tabCH Model Spec Value` s
        ON s.parent=m.name
        WHERE IFNULL(m.disabled,0)=0
    """

    params=[]

    if model_id:
        query+=" AND m.model_id=%s"
        params.append(model_id)

    return fetch_query(query,params)


def get_models_filtered_repo(
    item_group_id=None,
    category_id=None,
    sub_category_id=None,
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

    if category_id:
        query += " AND category_id=%s"
        params.append(category_id)

    if sub_category_id:
        query += " AND sub_category_id=%s"
        params.append(sub_category_id)

    if brand_id:
        query += " AND brand_id=%s"
        params.append(brand_id)

    query += " ORDER BY model_name"

    return fetch_query(query, params)


def get_model_distinct_attributes_repo(model_id):
    return fetch_query("""
        SELECT DISTINCT
            s.spec
        FROM `tabCH Model Spec Value` s
        JOIN `tabCH Model` m
            ON s.parent = m.name
        WHERE m.model_id=%s
        ORDER BY s.spec
    """, (model_id,))

def get_attribute_values_repo(model_id, spec):
    return fetch_query("""
        SELECT DISTINCT
            s.spec_value
        FROM `tabCH Model Spec Value` s
        JOIN `tabCH Model` m
            ON s.parent = m.name
        WHERE
            m.model_id=%s
            AND s.spec=%s
        ORDER BY s.spec_value
    """, (model_id, spec))

def get_items_repo(
    item_group_id,
    category_id,
    sub_category_id,
    brand_id,
    model_id,
    filters: dict
):
    conditions = []
    params = [
        item_group_id,
        category_id,
        sub_category_id,
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
            AND i.ch_category_id = %s
            AND i.ch_sub_category_id = %s
            AND i.ch_brand_id = %s
            AND i.ch_model_id = %s
            AND ({' OR '.join(conditions)})
        GROUP BY i.name, i.item_code, i.item_name
        HAVING COUNT(DISTINCT a.attribute) = %s
    """

    params.append(len(filters))

    return fetch_query(query, tuple(params))


def get_colors_by_storage_repo(model_id: int, storage_value: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT DISTINCT
                        color.spec_value AS color
                    FROM `tabCH Model Spec Value` storage
                    JOIN `tabCH Model Spec Value` color
                        ON storage.parent = color.parent
                    JOIN `tabCH Model` m
                        ON m.name = storage.parent
                    WHERE m.model_id = %s
                        AND storage.spec = 'Storage'
                        AND storage.spec_value = %s
                        AND color.spec = 'Colour'
                    ORDER BY color.spec_value
                    """,
                    (model_id, storage_value)
                )

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
            d_grade_oow_11
        FROM `tabBuyback Price Master`
        WHERE item_code = %s
    """, (item_code,))