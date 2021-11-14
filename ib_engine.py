
from sortedcontainers import SortedDict
from datetime import datetime
import logging

from ib_insync import *
from config import *
from tick import Tick

import threading

ib = IB()
ib.connect("127.0.0.1", 7497, clientId=23)


def get_market_price(symbol, currency):
    contracts = [Stock(symbol, "SMART", currency)]
    ib.qualifyContracts(*contracts)
    ib.reqMarketDataType(4)
    ib.reqMktData(contracts[0], '', False, False)
    ib.sleep(2)

    tick = ib.ticker(contracts[0])
    price = float(tick.marketPrice())

    return price


class EngineIBKR:

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
                if broker == "IBKR":
                    ib.sleep(1)
                    print(
                        "\n\n============================= IBKR Cycle begin! ========================================\n")
                    print(f"\nCurrent time: {datetime.now()}")
                    print(f"\nCurrent trades: {self.tickers}\n")

                    self.additional_order_trigger()
                    self.param_updated = self.update_params()
                    self.check_entry_trigger(self.param_updated)

                    print(
                        "\n\n============================== IBKR Cycle end! ======================================\n")
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

        contracts = [Stock(symbol, "SMART", currency)]
        ib.qualifyContracts(*contracts)
        side = "BUY" if direction == "LONG" else "SELL"
        reverse_side = "SELL" if side == "BUY" else "BUY"

        market_order = MarketOrder(side, size)
        try:
            if _ticker.init_entry.order.orderId == market_order.orderId:
                market_order.orderId += 1
        except Exception as e:
            print(e)
        _ticker.init_entry = ib.placeOrder(contracts[0], market_order)
        ib.reqExecutions()
        ib.sleep(4)

        if _ticker.init_entry.orderStatus.status == 'Filled' or _ticker.init_entry.orderStatus.filled == _ticker.size:
            _ticker.entry_filled = True
            _ticker.entry_price = _ticker.init_entry.orderStatus.avgFillPrice
            _ticker.average_entry_price = _ticker.entry_price
            _ticker.total_size = _ticker.size

            # current_price = get_market_price(symbol)
            # print(f"{symbol} - current market price: {current_price}")
            if side == "BUY":
                tp_price = round(_ticker.average_entry_price *
                                 (100 + _ticker.tp_level)/100, 2)
            else:
                tp_price = round(_ticker.average_entry_price *
                                 (100 - _ticker.tp_level) / 100, 2)
            tp_order = LimitOrder(reverse_side, size, tp_price)
            try:
                if _ticker.take_profit.order.orderId == tp_order.orderId:
                    tp_order.orderId += 1
            except Exception as e:
                print(e)
            _ticker.take_profit = ib.placeOrder(
                _ticker.init_entry.contract, tp_order)

        entry_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        _ticker.entry_time = entry_time

        self.tickers[key] = _ticker

    def additional_order_trigger(self):
        print("\n============== Checking for additional order =============")
        ib.reqExecutions()
        del_keys = []
        for key in self.tickers.keys():
            _ticker = self.tickers[key]
            if not _ticker.entry_filled and _ticker.init_entry.orderStatus.status == 'Filled':
                _ticker.entry_filled = True
                _ticker.entry_price = _ticker.init_entry.orderStatus.avgFillPrice
                _ticker.average_entry_price = _ticker.entry_price
                _ticker.total_size = _ticker.size
                if not _ticker.take_profit:
                    # current_price = get_market_price(_ticker.symbol)
                    reverse_side = "SELL" if _ticker.direction == "LONG" else "BUY"
                    size = _ticker.size
                    # print(f"{symbol} - current market price: {current_price}")
                    if _ticker.direction == "LONG":
                        tp_price = round(
                            _ticker.average_entry_price * (100 + _ticker.tp_level)/100, 2)
                    else:
                        tp_price = round(
                            _ticker.average_entry_price * (100 - _ticker.tp_level) / 100, 2)
                    tp_order = LimitOrder(reverse_side, size, tp_price)
                    try:
                        if _ticker.take_profit.order.orderId == tp_order.orderId:
                            tp_order.orderId += 1
                    except Exception as e:
                        print(e)
                    _ticker.take_profit = ib.placeOrder(
                        _ticker.init_entry.contract, tp_order)

            if not _ticker.entry_filled:
                continue

            if _ticker.exit_filled:
                print(f"{key} - take profit is already filled")
                del_keys.append(key)
                continue

            if _ticker.take_profit and _ticker.take_profit.orderStatus.status == 'Filled':
                _ticker.exit_filled = True
                _ticker.exit_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                del_keys.append(key)
                continue

            if _ticker.add_order:
                if len(list(_ticker.add_order.keys())) == _ticker.add_order_num:
                    print(
                        f"{key} - total number of additional orders already triggered.")
                    continue
                if len(list(_ticker.add_order.keys())) > 0:
                    current_add_order_key = sorted(
                        list(_ticker.add_order.keys()))[-1]
                    if _ticker.total_size != _ticker.take_profit.order.totalQuantity:
                        if _ticker.add_order[current_add_order_key].OrderStatus.status == "Filled":
                            new_average = _ticker.entry_price * _ticker.size
                            for i in range(1, current_add_order_key+1):
                                new_average = new_average + _ticker.add_order[i].orderStatus.avgFillPrice * \
                                    _ticker.add_size
                            new_average = round(
                                new_average / _ticker.total_size, 2)
                            _ticker.average_entry_price = new_average

                            if _ticker.direction == "LONG":
                                tp_price = round(
                                    _ticker.average_entry_price * (100 + _ticker.tp_level)/100, 2)
                            else:
                                tp_price = round(
                                    _ticker.average_entry_price * (100 - _ticker.tp_level) / 100, 2)
                            tp_order = _ticker.take_profit.order
                            tp_order.totalQuantity = _ticker.total_size
                            tp_order.lmtPrice = tp_price
                            _ticker.take_profit = ib.placeOrder(
                                _ticker.take_profit.contract, tp_order)
                            ib.sleep(4)

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

            current_price = get_market_price(_ticker.symbol, _ticker.currency)
            print(f"{_ticker.symbol} - current market price: {current_price}")
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
                    add_order = MarketOrder(side, _ticker.add_size)

                    _ticker.add_order[add_order_key] = ib.placeOrder(
                        _ticker.init_entry.contract, add_order)
                    _ticker.total_size = _ticker.total_size + _ticker.add_size
                    ib.sleep(4)

                    if _ticker.add_order[add_order_key].orderStatus.status == "Filled":
                        print(
                            f"{key} - {add_order_key}-th additional order gets filled")
                        print("updating average fill price and take profit order")
                        new_average = _ticker.entry_price * _ticker.size
                        for i in range(1, add_order_key+1):
                            new_average = new_average + _ticker.add_order[i].orderStatus.avgFillPrice * \
                                _ticker.add_size
                        new_average = round(
                            new_average / _ticker.total_size, 2)
                        _ticker.average_entry_price = new_average

                        if _ticker.direction == "LONG":
                            tp_price = round(
                                _ticker.average_entry_price * (100 + _ticker.tp_level)/100, 2)
                        else:
                            tp_price = round(
                                _ticker.average_entry_price * (100 - _ticker.tp_level) / 100, 2)
                        tp_order = _ticker.take_profit.order
                        tp_order.totalQuantity = _ticker.total_size
                        tp_order.lmtPrice = tp_price
                        _ticker.take_profit = ib.placeOrder(
                            _ticker.take_profit.contract, tp_order)
                        print(f"{key} - take profit order updated!")
                        ib.sleep(4)
