
class Tick(object):

    def __init__(self, symbol, currency, size, direction, tp_level, add_size, price_down_level, add_order_num):
        self.size = size
        self.symbol = symbol
        self.currency = currency
        self.direction = direction
        self.entry_time = ""
        self.exit_time = ""

        self.init_entry = None
        self.take_profit = None
        self.add_order = dict()
        self.add_order_num = add_order_num
        self.add_size = add_size
        self.tp_level = tp_level
        self.price_down_level = price_down_level

        self.exit_price = None
        self.entry_price = None
        self.entry_filled = False
        self.exit_filled = False

        self.average_entry_price = None
        self.total_size = None
