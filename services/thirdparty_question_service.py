from collections import OrderedDict

from repositories.thirdparty_question_repository import (
    get_thirdparty_buyback_questions_repo
)


def get_thirdparty_buyback_questions_service(item_code):

    rows = get_thirdparty_buyback_questions_repo(item_code)

    result = OrderedDict()

    for row in rows:

        qid = row["QuestionId"]

        if qid not in result:

            result[qid] = {
                "phyEvalId": row["QuestionId"],
                "productId": row["ProductId"],
                "flowId": "BuyBack",
                "elemType": "radio",
                "question": (row["question_text"] or "").strip(),
                "options": [],
                "prodCode": "MOB",
                "status": "active"
            }

        if row["option_value"] is not None:

            result[qid]["options"].append({
                "id": str(row["idx"]),
                "value": row["option_value"],
                "label": row["option_label"]
            })

    return {
        "success": True,
        "statusCode": 200,
        "msg": "Successfully Retrieved",
        "data": {
            "ticketQuePhy": list(result.values())
        }
    }