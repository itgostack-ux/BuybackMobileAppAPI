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


def get_manufacturers_repo():
    return fetch_query("""
        SELECT name,manufacturer_id,short_name,full_name
        FROM `tabManufacturer`
        WHERE IFNULL(ch_disabled,0)=0
        AND IFNULL(ch_is_active,0)=1
        ORDER BY manufacturer_id
    """)


def get_brands_repo(manufacturer=None):

    query="""
        SELECT name,brand_id,brand,ch_manufacturer
        FROM `tabBrand`
        WHERE IFNULL(ch_is_active,0)=1
    """

    params=[]

    if manufacturer:
        query+=" AND ch_manufacturer=%s"
        params.append(manufacturer)

    return fetch_query(query,params)


def get_models_repo(brand_id=None):

    query="""
        SELECT name,model_id,model_name,brand_id
        FROM `tabCH Model`
        WHERE IFNULL(disabled,0)=0
    """

    params=[]

    if brand_id:
        query+=" AND brand_id=%s"
        params.append(brand_id)

    return fetch_query(query,params)


def get_attributes_repo():
    return fetch_query("""
        SELECT name,attribute_name,numeric_values
        FROM `tabItem Attribute`
        WHERE IFNULL(disabled,0)=0
        ORDER BY attribute_name
    """)


def get_model_spec_values_repo(model_id=None):

    query="""
        SELECT m.model_id,m.model_name,
        s.spec,s.spec_value
        FROM `tabCH Model` m
        LEFT JOIN `tabCH Model Spec Value` s
        ON s.parent=m.name
        WHERE IFNULL(m.disabled,0)=0
    """

    params=[]

    if model_id:
        query+=" AND m.model_id=%s"
        params.append(model_id)

    return fetch_query(query,params)


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


def get_items_repo(params):

    return fetch_query("""
        SELECT DISTINCT i.item_code,i.item_name
        FROM `tabItem` i
        JOIN `tabItem Variant Attribute` a
        ON a.parent=i.name
        WHERE i.disabled=0
        AND i.ch_item_group_id=%s
        AND i.ch_category_id=%s
        AND i.ch_sub_category_id=%s
        AND i.ch_brand_id=%s
        AND i.ch_model_id=%s
        AND a.attribute=%s
        AND a.attribute_value=%s
    """,params)