from repositories.buyback_repository import fetch_buyback_details


def get_buyback_details(item_code=None, buyback_price_id=None):

    return fetch_buyback_details(item_code, buyback_price_id)