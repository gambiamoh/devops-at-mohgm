import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

import lots_fix_api as lots_fix_api


class LotFixApiTest(unittest.TestCase):

    @patch("lots_fix_api.make_request")
    def test_get_token(self, mock_make_request):
        mock_make_request.return_value = {"access_token": "test_token"}
        token = lots_fix_api.get_token(
            "base_url", {"Authorization": "auth_header"}, "username", "password"
        )
        self.assertEqual(token, "test_token")

    @patch("lots_fix_api.make_request")
    def test_get_data(self, mock_make_request):
        mock_make_request.return_value = "test_data"
        orderables, lots, inventories = lots_fix_api.get_data(
            "base_url", {"Authorization": "auth_header"}
        )
        self.assertEqual(orderables, "test_data")
        self.assertEqual(lots, "test_data")
        self.assertEqual(inventories, "test_data")

    @patch("lots_fix_api.make_request")
    @patch("pandas.read_csv")
    def test_process_data(self, mock_read_csv, mock_make_request):
        df = pd.DataFrame(
            {
                "orderableid": ["orderable1", "orderable2"],
                "tradeitemid": ["tradeitem1", "tradeitem2"],
                "lotcode": ["lot1", "lot2"],
            }
        )
        mock_read_csv.return_value = df
        orderables = [{"id": "orderable1", "identifiers": {"tradeItem": "tradeitem1"}}]
        lots = [{"id": "lot1", "lotCode": "lot1", "tradeItemId": "tradeitem1"}]
        inventories = [{"lineItems": [{"lotId": None, "orderableId": "orderable1"}]}]
        lots_fix_api.process_data(
            df,
            orderables,
            lots,
            inventories,
            "base_url",
            {"Authorization": "auth_header"},
        )
        mock_make_request.assert_called_with(
            "base_url/api/lots/lot1", {"Authorization": "auth_header"}, "put", lots[0]
        )


if __name__ == "__main__":
    unittest.main()
