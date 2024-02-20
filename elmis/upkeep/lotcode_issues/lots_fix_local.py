import json
import pandas as pd

"""
This is one of the scripts used to fix the lotCode/batchNumber mismatches
that occured after the Essential Medicines Master Data Upload by JSI TZ Team.
This is a local version of the script that reads the data from local files.

Local files:
- orderables.json: dump of the orderables from the orderables endpoint

- physicalInventories.json: dump of the physicalInventories from the physicalInventories endpoint

- orderables_tradeitems_lotcode.csv: CSV file containing the orderableId, productCode, lotCode, and tradeItemId 
from the DB.
"""
try:
    with open("data/orderables.json") as f:
        orderables = json.load(f)
except FileNotFoundError:
    print("orderables.json file not found.")
    exit(1)

try:
    with open("data/physicalInventories.json") as f:
        inventories = json.load(f)
except FileNotFoundError:
    print("physicalInventories.json file not found.")
    exit(1)

try:
    trade_items = pd.read_csv("data/orderables_tradeitems_lotcode.csv")
except FileNotFoundError:
    print("orderables_tradeitems_lotcode.csv file not found.")
    exit(1)

for inventory in inventories:
    for line_item in inventory["lineItems"]:
        if line_item["lotCode"] is None:
            orderable_id = line_item["orderableId"]

            for index, trade_item in trade_items.iterrows():
                if trade_item["orderableid"] == orderable_id:
                    product_code = trade_item["productCode"]
                    lot_code = trade_item["lotcode"]
                    trade_item_id = trade_item["tradeitemid"]

                    for orderable in orderables["content"]:
                        if orderable["productCode"] == product_code:
                            if orderable["identifiers"]["tradeItem"] != trade_item_id:
                                trade_items.loc[index, "tradeitemid"] = orderable[
                                    "identifiers"
                                ]["tradeItem"]

try:
    trade_items.to_csv("processed/fixed_tradeitems.csv", index=False)
except Exception as e:
    print(f"Error while saving CSV file: {e}")
