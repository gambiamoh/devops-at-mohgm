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


def get_token(base_url, headers, username, password):
    auth_response = make_request(
        f"{base_url}/api/oauth/token?grant_type=password",
        headers=headers,
        method="post",
        data={"username": username, "password": password},
    )
    return auth_response["access_token"]


def get_data(base_url, headers):
    facility = os.getenv("PHY_INV_FACILITY_ID")
    is_draft = os.getenv("PHY_INV_IS_DRAFT")
    program = os.getenv("PHY_INV_PROGRAM_ID")
    orderables = make_request(f"{base_url}/api/orderables", headers=headers)
    lots = make_request(f"{base_url}/api/lots", headers=headers)
    inventories = make_request(
        f"{base_url}/api/physicalInventories?facility={facility}&isDraft={is_draft}&program={program}",
        headers=headers,
    )
    return orderables, lots, inventories


def process_data(df, orderables, lots, inventories, base_url, headers):
    for inventory in inventories:
        for line_item in inventory["lineItems"]:
            if line_item["lotId"] is None:
                row = df[df["orderableid"] == line_item["orderableId"]]
                orderable = next(
                    (o for o in orderables if o["id"] == row["orderableid"].values[0]),
                    None,
                )

                if (
                    orderable
                    and orderable["identifiers"]["tradeItem"]
                    != row["tradeitemid"].values[0]
                ):
                    df.loc[
                        df["orderableid"] == line_item["orderableId"], "tradeitemid"
                    ] = orderable["identifiers"]["tradeItem"]

                    for lot in lots:
                        if (
                            lot["lotCode"] == row["lotcode"].values[0]
                            and lot["tradeItemId"] != row["tradeitemid"].values[0]
                        ):
                            lot["tradeItemId"] = row["tradeitemid"].values[0]
                            make_request(
                                f'{base_url}/api/lots/{lot["id"]}',
                                headers=headers,
                                method="put",
                                data=lot,
                            )


def main():
    """
    This is one of the scripts used to fix the lotCode/tradeItem mismatches
    that occured after the Essential Medicines Master Data upload.
    This is the version that gets data and makes update via the REST API.

    API Endpoints:
    - /orderables: all orderables

    - /physicalInventories: all physicalIventories

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

    df = pd.read_csv("data/orderables_tradeItems_lotCode.csv")

    try:
        orderables, lots, inventories = get_data(base_url, headers)
    except Exception as e:
        logging.error(f"Failed to get data: {e}")
        return

    try:
        process_data(df, orderables, lots, inventories, base_url, headers)
    except Exception as e:
        logging.error(f"Failed to process data: {e}")
        return

    df.to_csv("processed_tradeitems.csv", index=False)


if __name__ == "__main__":
    main()
