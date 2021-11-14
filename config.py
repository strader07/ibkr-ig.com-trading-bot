
import json

INIT_PRODUCT = "AAPL"
INIT_CURRENCY = "USD"
INIT_DIRECTION = "LONG"
INIT_ORDER_SIZE = "100"
INIT_ADDITIONAL_ORDER_SIZE = "30"
INIT_TP_LEVEL = "1.5"
INIT_NUM_ADD_ORDER = "3"
INIT_PRICE_DOWN_LEVEL = "1.5"


class Config:

    def __init__(self):
        try:
            with open("settings/params.json", "r") as f:
                params = json.load(f)
        except:
            params = {}
        if not params:
            params = {
                "product": INIT_PRODUCT,
                "currency": INIT_CURRENCY,
                "direction": INIT_DIRECTION,
                "init_size": INIT_ORDER_SIZE,
                "add_size": INIT_ADDITIONAL_ORDER_SIZE,
                "tp_level": INIT_TP_LEVEL,
                "num_add_order": INIT_NUM_ADD_ORDER,
                "price_down_level": INIT_PRICE_DOWN_LEVEL
            }

        self.params = params

    def update_params(self):
        try:
            with open("settings/params.json", "r") as f:
                params = json.load(f)
        except:
            params = {}
        if not params:
            params = {
                "product": INIT_PRODUCT,
                "currency": INIT_CURRENCY,
                "direction": INIT_DIRECTION,
                "init_size": INIT_ORDER_SIZE,
                "add_size": INIT_ADDITIONAL_ORDER_SIZE,
                "tp_level": INIT_TP_LEVEL,
                "num_add_order": INIT_NUM_ADD_ORDER,
                "price_down_level": INIT_PRICE_DOWN_LEVEL
            }

        self.params = params
