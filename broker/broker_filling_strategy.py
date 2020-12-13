class BaseFillingStrategy(object):
    def __init__(self):
        return
    
    def execute_order(self, order):
        if order.isIdle() or order.isClosed():
            return None, None
        if order.isBuyLong():
            return self.execute_buy_long_order(order)
        elif order.isSellLong():
            return self.execute_sell_long_order(order)
        elif order.isBuyShort():
            return self.execute_buy_short_order(order)
        elif order.isSellShort():
            return self.execute_sell_short_order(order)
        else:
            raise TypeError
    
    def execute_buy_long_order(self, order):
        raise NotImplementedError
    
    def execute_sell_long_order(self, order):
        raise NotImplementedError
    
    def execute_buy_short_order(self, order):
        raise NotImplementedError
    
    def execute_sell_short_order(self, order):
        raise NotImplementedError

class SimpleFillingStrategy(BaseFillingStrategy):
    def execute_buy_long_order(self, order):
        candle = order.candle_feed.value
        if order.stop is None or order.stop.price is None:
            if order.limit is None or order.limit.price is None:
                price = candle.open
            else:
                price = min(candle.open, order.limit.price)
        else:
            stop = order.stop.price
            if candle.open > stop:
                if order.limit is None or order.limit.price is None:
                    price = candle.open
                else:
                    price = min(candle.open, order.limit.price)
            else:
                price = stop
        quantity = order.quantity
        return price, quantity
    
    def execute_sell_long_order(self, order):
        candle = order.candle_feed.value
        if order.stop is None or order.stop.price is None:
            if order.limit is None or order.limit.price is None:
                price = candle.open
            else:
                price = max(candle.open, order.limit.price)
        else:
            stop = order.stop.price
            if candle.open < stop:
                if order.limit is None or order.limit.price is None:
                    price = candle.open
                else:
                    price = max(candle.open, order.limit.price)
            else:
                price = stop
        quantity = order.quantity
        return price, quantity
