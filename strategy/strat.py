from ..math import MACDSignal, Crossover
from ..broker.order import BuyLongOrder, SellLongOrder
from ..depot.position import Position


class BaseStrategy(object):
    def __init__(self, broker, depot, candle_feeds=None):
        self.broker = broker
        self.depot = depot
        self.positions = []
        candle_feeds = candle_feeds if candle_feeds is not None else []
        self.candle_feeds = []
        for cf in candle_feeds:
            self.add_candle_feed(cf)
    
    def update(self):
        new_pos = []
        for pos in self.positions:
            if pos in self.depot:
                new_pos.append(pos)
        self.positions = new_pos
        return
    
    def add_candle_feed(self, candle_feed):
        if candle_feed in self.broker:
            self.candle_feeds.append(candle_feed)
    
    def suggest_orders(self):
        raise NotImplementedError


class MACDStrat(BaseStrategy):
    def __init__(self, broker, depot, candle_feeds=None):
        self.crosses_above = []
        self.crosses_below = []
        super().__init__(broker, depot, candle_feeds=candle_feeds)
    
    def add_candle_feed(self, candle_feed):
        if candle_feed in self.broker:
            self.candle_feeds.append(candle_feed)
            signal = MACDSignal(candle_feed.close)
            macd = signal.macd
            self.crosses_below.append(Crossover(signal, macd, from_above=False))
            self.crosses_above.append(Crossover(signal, macd, from_below=False))
    
    def suggest_orders(self):
        orders = []
        for pos in self.positions:
            cf = pos.candle_feed
            op = pos.open_price
            if cf.value.low < op * 0.9 or cf.value.high > op * 1.15:
                order = SellLongOrder(pos, pos.size)
                orders.append(order)
        for cf, below, above in zip(self.candle_feeds,
                                    self.crosses_below,
                                    self.crosses_above):
            below.set_head_or_prior(self.broker.current_dateindex)
            above.set_head_or_prior(self.broker.current_dateindex)
            if below.value:
                pos = Position(cf, amount=0)
                num = int((self.depot.value() * 0.01) / (cf.value.high * 0.1))
                if num > 0:
                    order = BuyLongOrder(pos, num)
                    orders.append(order)
                    self.positions.append(pos)
        return orders
