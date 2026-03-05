from core.database import get_db_connection
from pymysql.cursors import DictCursor


def fetch_buyback_details(item_code=None, buyback_price_id=None):

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
        WHERE 1=1
    """

    params = []

    if item_code:
        query += " AND item_code = %s"
        params.append(item_code)

    if buyback_price_id:
        query += " AND buyback_price_id = %s"
        params.append(buyback_price_id)

    # Correct way to use context manager
    with get_db_connection() as conn:
        cursor = conn.cursor(DictCursor)
        cursor.execute(query, params)
        result = cursor.fetchone()

    return result