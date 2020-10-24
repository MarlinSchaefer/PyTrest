import datetime
from ..types import DictList
from ..currency import Money

class Position(object):
    def __init__(self, candle_feed, dateindex=None, amount=1,
                 currency='USD', open_price=None, evaluate_at='low',
                 position_type='long'):
        self.candle_feed = candle_feed
        
        if dateindex is None:
            dateindex = self.candle_feed.dateindex
        assert isinstance(dateindex, datetime.datetime)
        self.open_date = dateindex
        
        self.reduce_history = DictList()
        self.currency = currency
        
        assert isinstance(amount, int) and amount > 0
        self.open_amount = amount
        self.amount = amount
        
        self.evaluate_at = evaluate_at
        
        self.currency = currency
        
        if open_price is None:
            self.open_price = self.candle_feed[self.open_date].get_by_name(self.evaluate_at)
        else:
            if isinstance(open_price, Money):
                self.open_price = open_price.convert(self.currency,
                                                     date=self.open_date)
            else:
                self.open_price = Money(open_price,
                                        currency=self.currency)
        
        if not isinstance(position_type, str):
            raise TypeError
        if not position_type in ['long', 'short']:
            raise ValueError
        self.position_type = position_type.lower()
    
    @property
    def size(self):
        return self.amount
    
    def reduce_position_size(self, amount, dateindex=None,
                             price=None):
        reduce_dates = list(self.reduce_history.keys())
        if len(reduce_dates) > 0:
            if dateindex < max(reduce_list):
                msg = 'Cannot reduce position size for a Position that '
                msg += 'was reduced at a later date already.'
                raise ValueError(msg)
        assert isinstance(amount, int) and amount > 0
        if amount > self.amount:
            amount = self.amount
        
        if price is None:
            price = self.candle_feed[dateindex].get_by_name(self.evaluate_at)
        
        found_matching = None
        
        if dateindex in self.reduce_history:
            for i, (amount, old_price) in enumerate(self.reduce_history[dateindex]):
                if price == old_price:
                    found_matching = i
            if found_matching is not None:
                self.reduce_history[dateindex][found_matching][0] += amount
        if found_matching is None:
            if price is None:
                price = self.candle_feed[dateindex].get_by_name(self.evaluate_at)
            self.reduce_history.append({dateindex: [amount, price]})
        
        self.amount -= amount
        if self.position_type == 'long':
            return price * amount
        elif self.position_type == 'short':
            return -price * amount
        else:
            raise RuntimeError
    
    def value(self):
        val = self.amount * self.candle_feed.value_by_name(self.evaluate_at)
        return Money(val, currency=self.currency)
    
    @property
    def returns(self):
        start_val = self.open_amount * self.open_price
        cur_val = Money(0., currency=self.currency)
        for datehistory in self.reduce_history.values():
            for reduce_info in datehistory:
                cur_val += (reduce_info[0] * reduce_info[1])
        cur_val += self.value()
        if self.position_type == 'long':
            return cur_val - start_val
        elif self.position_type == 'short':
            return start_val - cur_val
        else:
            raise RuntimeError
        
    pass
