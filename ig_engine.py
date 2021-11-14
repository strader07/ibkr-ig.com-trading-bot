
from sortedcontainers import SortedDict
from datetime import datetime
import logging
import time
import threading
import sys

from config import *
from tick import Tick

from trading_ig import IGService
from trading_ig.config import config as ig_config

ig_service = IGService(ig_config.username, ig_config.password,
                       ig_config.api_key, ig_config.acc_type)
accountId = ig_config.acc_number
try:
    ig_service.switch_account(accountId, True)
    print("Successfully switched the default account to {}".format(accountId))
except:
    print("Your account {} has been already set as default".format(accountId))

while True:
    try:
        ig_service.create_session()
        print("Session created!")
        break
    except Exception as e:
        print(e)
        time.sleep(1)
        continue


class EngineIG:

    def __init__(self):
        self.config = Config()
        self.tickers = SortedDict()
        self.dfs = {}
        self.params = {}
        self.param_updated = True
        self.app_status = "OFF"
        try:
            with open("settings/app_status.txt", "w") as fp:
                fp.write(self.app_status)
                fp.close()
        except:
            pass

    def run_cycle(self):
        while True:
            th_names = [th.name for th in threading.enumerate()]
            if "Thread-1" not in th_names:
                sys.exit()
            if self.app_status == "ON":
                with open("settings/broker", "r") as f:
                    broker = f.readlines()[0]
                if broker == "IG":
                    time.sleep(1)
                    print(
                        "\n\n============================= IG Cycle begin! ========================================\n")
                    print(f"\nCurrent time: {datetime.now()}")
                    print(f"\nCurrent trades: {self.tickers}\n")

                    self.additional_order_trigger()
                    self.param_updated = self.update_params()
                    self.check_entry_trigger(self.param_updated)

                    print(
                        "\n\n============================== IG Cycle end! ======================================\n")
            if self.app_status == "OFF":
                self.tickers = SortedDict()

            try:
                with open("settings/app_status.txt", "r") as fp:
                    self.app_status = fp.readlines()[0]
            except:
                self.app_status = "OFF"
                self.tickers = SortedDict()

    def update_params(self):
        self.config.update_params()
        if self.params != self.config.params:
            self.params = self.config.params
            print(f"Parameters updated: {self.params}\n")
            return True
        else:
            print(f"Parameters unchanged: {self.params}\n")
            return False

    def check_entry_trigger(self, param_updated):
        print("\n============== Checking for a new entry long/short =============")
        params = self.params
        key = f"{params['product']}_{params['direction']}"
        if param_updated or key not in self.tickers.keys():
            print("There comes a new ticker.")
            logging.getLogger().debug("There comes a new ticker.")
            self.enter_trades(params)

    def enter_trades(self, params):
        print(params)
        symbol = params["product"]
        currency = params["currency"]
        size = int(params["init_size"])
        direction = params["direction"]
        tp_level = float(params["tp_level"])
        add_size = int(params["add_size"])
        add_order_num = int(params["add_order_num"])
        price_down_level = float(params["price_down_level"])
        _ticker = Tick(symbol, currency, size, direction, tp_level,
                       add_size, price_down_level, add_order_num)
        key = f"{symbol}_{direction}"

        side = "BUY" if direction == "LONG" else "SELL"
        try:
            res_create = ig_service.create_open_position(
                currency_code=currency,
                direction=side,
                epic=symbol,
                expiry='-',
                force_open=True,
                guaranteed_stop=False,
                level=None,
                order_type='MARKET',
                size=size,
                stop_distance=None,
                limit_distance=None,
                limit_level=None,
                quote_id=None,
                stop_level=None,
                trailing_stop=None,
                trailing_stop_increment=None)
        except Exception as e:
            print(e)
            return None

        if res_create["dealStatus"] == "REJECTED":
            print(res_create)
            return None

        print(res_create)
        _ticker.init_entry = res_create
        if _ticker.init_entry["reason"] == 'SUCCESS':
            _ticker.entry_filled = True
            _ticker.entry_price = _ticker.init_entry["level"]
            _ticker.average_entry_price = _ticker.entry_price
            _ticker.total_size = _ticker.size
            entry_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            _ticker.entry_time = entry_time

            if side == "BUY":
                tp_price = round(_ticker.average_entry_price *
                                 (100 + _ticker.tp_level)/100, 1)
            else:
                tp_price = round(_ticker.average_entry_price *
                                 (100 - _ticker.tp_level) / 100, 1)
            deal_id = _ticker.init_entry["dealId"]

            res_update = ig_service.update_open_position(
                tp_price, None, deal_id, None)
            _ticker.take_profit = res_update
            print(res_update)

            self.tickers[key] = _ticker

    def additional_order_trigger(self):
        print("\n============== Checking for additional order =============")
        del_keys = []
        for key in self.tickers.keys():
            _ticker = self.tickers[key]
            try:
                positions = ig_service.fetch_open_positions()[
                    "position"].tolist()
                positions = [
                    position for position in positions if position["dealId"] == _ticker.init_entry["dealId"]]
                if len(positions) == 0:
                    continue
                position = positions[0]
                if not _ticker.take_profit:
                    if _ticker.direction == "LONG":
                        tp_price = round(
                            _ticker.average_entry_price * (100 + _ticker.tp_level)/100, 1)
                    else:
                        tp_price = round(
                            _ticker.average_entry_price * (100 - _ticker.tp_level) / 100, 1)
                    deal_id = _ticker.init_entry["dealId"]

                    res_update = ig_service.update_open_position(
                        tp_price, None, deal_id, None)
                    _ticker.take_profit = res_update
            except Exception as e:
                print(f"{key} - getting position error - {e}")
                positions = []
                continue

            if not _ticker.entry_filled:
                continue

            if _ticker.exit_filled:
                print(f"{key} - take profit is already filled")
                del_keys.append(key)
                continue

            if _ticker.take_profit:
                if len(positions) == 0:
                    _ticker.exit_filled = True
                    _ticker.exit_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                    del_keys.append(key)
                    continue

        # for key in del_keys:
        #     del self.tickers[key]

        for key in self.tickers.keys():
            _ticker = self.tickers[key]
            if not _ticker.entry_filled:
                print(f"{key} - entry is not filled")
                continue

            if _ticker.exit_filled:
                print(f"{key} - take profit is already filled")
                continue

            if _ticker.add_order:
                if len(list(_ticker.add_order.keys())) == _ticker.add_order_num:
                    print(
                        f"{key} - total number of additional orders already triggered.")
                    continue

            try:
                current_market = ig_service.fetch_market_by_epic(
                    _ticker.init_entry["epic"])['snapshot']
            except Exception as e:
                print(e)
                continue
            if _ticker.direction == 'LONG':
                current_price = current_market['offer']
            else:
                current_price = current_market['bid']
            print(f"{key} - current market price: {current_price}")
            print(f"{key} - average entry price: {_ticker.average_entry_price}")
            try:
                current_add_order_key = sorted(
                    list(_ticker.add_order.keys()))[-1]
            except:
                current_add_order_key = 0
            print(current_add_order_key)

            if current_add_order_key < _ticker.add_order_num:
                if _ticker.direction == "LONG":
                    down_triggered = current_price <= _ticker.average_entry_price * \
                        (100 - _ticker.price_down_level) / 100
                    side = "BUY"
                else:
                    down_triggered = current_price >= _ticker.average_entry_price * \
                        (100 + _ticker.price_down_level) / 100
                    side = "SELL"
                if down_triggered:
                    print(f"{key} - enter a new additional order")
                    add_order_key = current_add_order_key + 1
                    try:
                        res_create = ig_service.create_open_position(
                            currency_code=_ticker.currency,
                            direction=side,
                            epic=_ticker.symbol,
                            expiry='-',
                            force_open=True,
                            guaranteed_stop=False,
                            level=None,
                            order_type='MARKET',
                            size=_ticker.add_size,
                            stop_distance=None,
                            limit_distance=None,
                            limit_level=None,
                            quote_id=None,
                            stop_level=None,
                            trailing_stop=None,
                            trailing_stop_increment=None)
                    except Exception as e:
                        print(e)
                        continue

                    if res_create["dealStatus"] == "REJECTED":
                        print(res_create)
                        continue

                    if res_create["reason"] == "SUCCESS":
                        _ticker.add_order[add_order_key] = res_create
                        _ticker.total_size = _ticker.total_size + _ticker.add_size
                        print(
                            f"{key} - updating average fill price and take profit order")
                        new_average = _ticker.entry_price * _ticker.size
                        for i in range(1, add_order_key+1):
                            new_average = new_average + _ticker.add_order[i]["level"] * \
                                _ticker.add_size
                        new_average = round(
                            new_average / _ticker.total_size, 1)
                        _ticker.average_entry_price = new_average

                        if _ticker.direction == "LONG":
                            tp_price = round(
                                _ticker.average_entry_price * (100 + _ticker.tp_level)/100, 2)
                        else:
                            tp_price = round(
                                _ticker.average_entry_price * (100 - _ticker.tp_level) / 100, 2)

                        res_update = ig_service.update_open_position(
                            tp_price, None, _ticker.init_entry["dealId"], None)
                        _ticker.take_profit = res_update

                        for i in range(1, add_order_key+1):
                            _ticker.add_order[i] = ig_service.update_open_position(
                                tp_price, None, _ticker.add_order[i]["dealId"], None)
