from core.database import get_db_connection


def fetch_query(query, params=None):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or [])
            return cursor.fetchall()


def get_device_items_repo():
    return fetch_query("""
        SELECT name, item_group_id, item_group_name, parent_item_group,
               is_group, lft, rgt
        FROM `tabItem Group`
        WHERE IFNULL(ch_disabled,0)=0
        AND IFNULL(ch_is_active,0)=1
        AND item_group_name = 'Mobiles'
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



def get_brands_by_subcategory_repo(item_group_id=None):
    query = """
        SELECT DISTINCT
            m.brand_id,
            m.brand
        FROM `tabCH Model` m
        WHERE IFNULL(m.disabled,0)=0
        AND IFNULL(m.brand,'') != ''
    """

    params = []

    if item_group_id:
        query += " AND m.item_group_id=%s"
        params.append(item_group_id)

    query += " ORDER BY m.brand ASC"

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
    brand_id=None
):
    query = """
        SELECT
            m.name,
            m.model_id,
            m.model_name,
            m.brand,
            m.brand_id,
            ig.item_group_name
        FROM `tabCH Model` AS m

        LEFT JOIN `tabItem Group` AS ig
            ON ig.item_group_id = m.item_group_id

        WHERE IFNULL(m.disabled, 0) = 0
    """

    params = []

    if item_group_id:
        query += " AND m.item_group_id = %s"
        params.append(item_group_id)

    if brand_id:
        query += " AND m.brand_id = %s"
        params.append(brand_id)

    query += " ORDER BY m.model_name"

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
            {"AND (" + " OR ".join(conditions) + ")" if conditions else ""}
        GROUP BY i.name, i.item_code, i.item_name
        { "HAVING COUNT(DISTINCT a.attribute) = %s" if conditions else "" }
    """

    if conditions:
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
    import re

import re

import re


def get_variants_by_model_storage_repo(device_name):
    """
    Examples:
    ----------
    poco f4 5g 8gb 128gb
    Apple iPhone 11 128GB
    samsung s23 ultra 12gb 256gb
    """

    text = (device_name or "").lower().strip()

    # ------------------------------------------------
    # Extract RAM & STORAGE
    # ------------------------------------------------
    gb_values = re.findall(
        r'(\d+\s*(?:gb|tb))',
        text,
        re.IGNORECASE
    )

    ram = None
    storage = None

    cleaned_gb_values = []

    for value in gb_values:

        cleaned_value = value.replace(
            " ",
            ""
        ).lower()

        cleaned_gb_values.append(cleaned_value)

    if len(cleaned_gb_values) >= 2:

        ram = cleaned_gb_values[0]
        storage = cleaned_gb_values[1]

    elif len(cleaned_gb_values) == 1:

        storage = cleaned_gb_values[0]

    # ------------------------------------------------
    # Remove RAM/STORAGE from Search
    # ------------------------------------------------
    clean_text = re.sub(
        r'\d+\s*(gb|tb)',
        '',
        text,
        flags=re.IGNORECASE
    )

    clean_text = clean_text.replace("-", " ")
    clean_text = clean_text.replace("_", " ")

    clean_text = " ".join(
        clean_text.split()
    )

    # ------------------------------------------------
    # Dynamic Search
    # ------------------------------------------------
    words = clean_text.split()

    conditions = []
    values = []

    for word in words:

        conditions.append("""
            (
                LOWER(i.item_name) LIKE %s
                OR LOWER(IFNULL(i.brand, '')) LIKE %s
                OR LOWER(IFNULL(m.model_name, '')) LIKE %s
                OR LOWER(IFNULL(i.ch_sub_category, '')) LIKE %s
                OR LOWER(IFNULL(i.ch_category, '')) LIKE %s
                OR LOWER(IFNULL(i.ch_model, '')) LIKE %s
            )
        """)

        like_value = f"%{word}%"

        values.extend([
            like_value,
            like_value,
            like_value,
            like_value,
            like_value,
            like_value
        ])

    dynamic_sql = " AND ".join(conditions)

    # ------------------------------------------------
    # Final Query
    # ------------------------------------------------
    query = f"""
        SELECT DISTINCT

            i.item_code,
            i.item_name,
            i.brand,
            i.ch_category,
            i.ch_sub_category,
            i.ch_model,

            m.model_name,

            ram_attr.attribute_value AS ram,
            storage_attr.attribute_value AS storage,
            color.attribute_value AS color

        FROM `tabItem` i

        LEFT JOIN `tabCH Model` m
            ON m.model_id = i.ch_model_id

        LEFT JOIN `tabItem Variant Attribute` ram_attr
            ON ram_attr.parent = i.item_code
            AND ram_attr.attribute = 'RAM'

        LEFT JOIN `tabItem Variant Attribute` storage_attr
            ON storage_attr.parent = i.item_code
            AND storage_attr.attribute = 'Storage'

        LEFT JOIN `tabItem Variant Attribute` color
            ON color.parent = i.item_code
            AND color.attribute = 'Colour'

        WHERE
            i.disabled = 0
    """

    # ------------------------------------------------
    # Dynamic Search Filter
    # ------------------------------------------------
    if dynamic_sql:
        query += f" AND ({dynamic_sql})"

    # ------------------------------------------------
    # RAM Filter
    # ------------------------------------------------
    query += """
        AND (
            %s IS NULL

            OR LOWER(IFNULL(ram_attr.attribute_value, ''))
                = LOWER(%s)
        )
    """

    # ------------------------------------------------
    # STORAGE Filter
    # ------------------------------------------------
    query += """
        AND (
            %s IS NULL

            OR LOWER(IFNULL(storage_attr.attribute_value, ''))
                = LOWER(%s)
        )
    """

    # ------------------------------------------------
    # Order
    # ------------------------------------------------
    query += """
        ORDER BY
            i.item_name ASC
    """

    # ------------------------------------------------
    # Params
    # ------------------------------------------------
    params = (
        values
        + [
            ram,
            ram,

            storage,
            storage
        ]
    )

    return fetch_query(
        query,
        tuple(params)
    )

def get_model_variants_repo(
    model_id,
    attributes
):

    # -----------------------------------
    # Single Attribute
    # -----------------------------------
    if len(attributes) == 1:

        query = """
            SELECT DISTINCT

                s.spec_value AS storage,
                s.spec_value AS variant

            FROM `tabCH Model Spec Value` s

            INNER JOIN `tabCH Model` m
                ON m.name = s.parent

            WHERE
                m.model_id = %s
                AND s.spec = %s

            ORDER BY s.spec_value
        """

        return fetch_query(
            query,
            (
                model_id,
                attributes[0]
            )
        )

    # -----------------------------------
    # RAM + STORAGE
    # -----------------------------------
    elif len(attributes) == 2:

        query = """
            SELECT DISTINCT

                a.spec_value AS ram,
                b.spec_value AS storage,

                CONCAT(
                    a.spec_value,
                    ' / ',
                    b.spec_value
                ) AS variant

            FROM `tabCH Model Spec Value` a

            INNER JOIN `tabCH Model Spec Value` b
                ON a.parent = b.parent

            INNER JOIN `tabCH Model` m
                ON m.name = a.parent

            WHERE
                m.model_id = %s
                AND a.spec = %s
                AND b.spec = %s

            ORDER BY
                a.spec_value,
                b.spec_value
        """

        return fetch_query(
            query,
            (
                model_id,
                attributes[0],
                attributes[1]
            )
        )

    return []


def get_variants_by_ram_storage_repo(
    model_id,
    ram=None,
    storage=None
):

    query = """
        SELECT DISTINCT

            ram.spec_value AS ram,
            storage.spec_value AS storage,
            color.spec_value AS color

        FROM `tabCH Model` m

        LEFT JOIN `tabCH Model Spec Value` ram
            ON ram.parent = m.name
            AND ram.spec = 'RAM'

        LEFT JOIN `tabCH Model Spec Value` storage
            ON storage.parent = m.name
            AND storage.spec = 'Storage'

        LEFT JOIN `tabCH Model Spec Value` color
            ON color.parent = m.name
            AND color.spec = 'Colour'

        WHERE
            m.model_id = %s
    """

    params = [model_id]

    # -----------------------------
    # RAM FILTER
    # -----------------------------
    if ram:
        query += """
            AND ram.spec_value = %s
        """
        params.append(ram)

    # -----------------------------
    # STORAGE FILTER
    # -----------------------------
    if storage:
        query += """
            AND storage.spec_value = %s
        """
        params.append(storage)

    # -----------------------------
    # ORDER
    # -----------------------------
    query += """
        ORDER BY
            ram.spec_value,
            storage.spec_value,
            color.spec_value
    """

    return fetch_query(
        query,
        tuple(params)
    )