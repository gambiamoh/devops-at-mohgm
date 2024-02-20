import os
import time
import requests
import pandas as pd
import json
import logging
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def make_request(url, headers, method="get", data=None):
    try:
        if method == "get":
            response = requests.get(url, headers=headers)
        elif method == "post":
            response = requests.post(url, headers=headers, data=data)
        elif method == "put":
            response = requests.put(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        raise
    return response.json()


def load_credentials():
    load_dotenv()
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    base_url = os.getenv("BASE_URL")
    auth_header = os.getenv("AUTH_HEADER")
    if not all([username, password, base_url, auth_header]):
        raise Exception("Missing required environment variables")
    return username, password, base_url, auth_header


def load_headers():
    try:
        username, password, base_url, auth_header = load_credentials()
        headers = {"Authorization": auth_header}
        token = get_token(base_url, headers, username, password)
        headers["Authorization"] = f"Bearer {token}"
        headers["Content-Type"] = "application/json"
        return headers
    except Exception as e:
        logging.error(f"Failed to get token: {e}")
        return None


def get_token(base_url, headers, username, password):
    auth_response = make_request(
        f"{base_url}/api/oauth/token?grant_type=password",
        headers=headers,
        method="post",
        data={"username": username, "password": password},
    )
    return auth_response["access_token"]


def get_data():
    # reading reference data from local dumps
    with open("data/orderables.json", "r") as f:
        orderables = json.load(f)["content"]
    with open("data/lots.json", "r") as f:
        lots = json.load(f)["content"]
    with open("data/physicalInventories.json", "r") as f:
        inventories = json.load(f)

    return orderables, lots, inventories


def process_data(df, orderables, lots, inventories, base_url, headers):
    df_orderables = pd.DataFrame(orderables)
    df_lots = pd.DataFrame(lots)

    for inventory in inventories:
        for line_item in inventory["lineItems"]:
            if line_item["lotId"] is None:
                row = df[df["orderableid"] == line_item["orderableId"]]

                if not row.empty:
                    product_code = row["productCode"].values[0]
                    lot_code = row["lotcode"].values[0]
                    csv_trade_item_id = row["tradeitemid"].values[0]

                    orderable = df_orderables[
                        df_orderables["productCode"] == product_code
                    ].iloc[0]
                    orderable_trade_item_id = orderable["identifiers"]["tradeItem"]

                    if csv_trade_item_id != orderable_trade_item_id:
                        df.loc[df["productCode"] == product_code, "tradeitemid"] = (
                            orderable_trade_item_id
                        )

                        for lot in lots:
                            if (
                                lot["lotCode"] == lot_code
                                and lot["tradeItemId"] != orderable_trade_item_id
                            ):
                                lot["tradeItemId"] = orderable_trade_item_id

    with open("updated_lots.json", "w") as f:
        json.dump(lots, f)
    print(headers)

    for i, lot in enumerate(lots):
        try:
            make_request(
                f"{base_url}/api/lots/{lot['id']}",
                headers=headers,
                method="put",
                data=lot,
            )
            logging.info(f"Successfully updated lot {i+1} of {len(lots)}")
        except Exception as e:
            logging.error(f"Failed to update lot {lot['id']}: {str(e)}, {headers}")


def main():
    """
    This is one of the scripts used to fix the lotCode/tradeItem mismatches
    that occured after the Essential Medicines Master Data upload.
    This is the version that gets data and makes update via the REST API.

    Local files:
    - orderables.json: all orderables from /orderables endpoint

    - physicalInventories.json: all physicalIventories from /physicalInventories endpoint

    - lots.json: all lots from /lots endpoint

    - orderables_tradeitems_lotcode.csv: CSV file containing the orderableId, productCode, lotCode, and tradeItemId
    from the DB.
    """
    try:
        username, password, base_url, auth_header = load_credentials()
        headers = {"Authorization": auth_header}
        token = get_token(base_url, headers, username, password)
    except Exception as e:
        logging.error(f"Failed to get token: {e}")
        return

    headers["Authorization"] = f"Bearer {token}"
    headers["Content-Type"] = "application/json"

    df = pd.read_csv("data/orderables_tradeItems_lotCode.csv")

    try:
        orderables, lots, inventories = get_data()
    except Exception as e:
        logging.error(f"Failed to get data: {e}")
        return

    try:
        process_data(df, orderables, lots, inventories, base_url, headers)
    except Exception as e:
        logging.error(f"Failed to process data: {e}")
        return

    print(lots)
    df.to_csv("processed_tradeitems.csv", index=False)


if __name__ == "__main__":
    main()
