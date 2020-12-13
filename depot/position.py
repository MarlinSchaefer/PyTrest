import datetime
from ..types import DateSeries
from ..currency import Money

class PositionHistory(DateSeries):
    def size_event(self, item, dateindex, msg=None):
        if msg is None:
            msg = 'Unnamed position size movement'
        msg = str(msg)
        if dateindex not in self:
            self.insert_value(dateindex, value=[])
        self.loc(dateindex).append([item, msg])

class Position(object):
    def __init__(self, candle_feed, dateindex=None, amount=1,
                 currency='USD', open_price=None, evaluate_at='low',
                 position_type='long'):
        self.candle_feed = candle_feed
        
        if dateindex is None:
            dateindex = self.candle_feed.dateindex
        assert isinstance(dateindex, datetime.datetime)
        self.open_date = dateindex
        
        self.history = PositionHistory()
        self.currency = currency
        
        assert isinstance(amount, int) and amount >= 0
        self.initiated = amount > 0
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
        if not position_type.lower() in ['long', 'short']:
            raise ValueError
        self.position_type = position_type.lower()
    
    @property
    def size(self):
        return self.amount
    
    def record_history(self, dateindex, amount, price, msg=None):
        if self.history.max_dateindex is not None:
            assert dateindex >= max(self.history.index), 'Cannot alter position in the past.'
        self.history.size_event([amount, price], dateindex, msg=msg)
    
    def reduce_position_size(self, amount, dateindex=None,
                             price=None):
        if not self.initiated:
            raise RuntimeError('Position must be initiated before it can be reduced.')
        if dateindex is None:
            dateindex = self.candle_feed.dateindex
        assert isinstance(amount, int) and amount > 0
        if amount > self.amount:
            amount = self.amount
        
        if price is None:
            price = self.candle_feed[dateindex].get_by_name(self.evaluate_at)
        
        self.record_history(dateindex, -amount, price, msg='Size reduction')
        
        self.amount -= amount
        if self.position_type == 'long':
            return price * amount
        elif self.position_type == 'short':
            return -price * amount
        else:
            raise RuntimeError
    
    def increase_position_size(self, amount, dateindex=None,
                             price=None):
        if dateindex is None:
            dateindex = self.candle_feed.dateindex
        assert isinstance(amount, int) and amount > 0
        
        if price is None:
            price = self.candle_feed[dateindex].get_by_name(self.evaluate_at)
        
        self.record_history(dateindex, amount, price, msg='Size increase')
        
        self.amount += amount
        if not self.initiated and self.amount > 0:
            self.initiated = True
            self.open_amount = amount
            self.open_price = price
            self.open_date = dateindex
        if self.position_type == 'long':
            return -price * amount
        elif self.position_type == 'short':
            return price * amount
        else:
            raise RuntimeError
    
    def value(self, currency=None):
        val = self.amount * self.candle_feed.value_by_name(self.evaluate_at)
        if currency is None:
            return Money(val, currency=self.currency)
        else:
            return Money(val, currency=self.currency).convert(currency)
    
    @property
    def price(self):
        price = self.candle_feed.value_by_name(self.evaluate_at)
        return Money(price, currency=self.currency)
    
    @property
    def returns(self):
        if not self.initiated:
            return Money(0., currency=self.currency)
        start_value = self.open_amount * self.open_price
        current_size = self.open_amount
        sold_value = 0.
        for dateindex in self.history.index:
            pos_changes = self.history.loc(dateindex)
            for ((amount, price), _) in pos_changes:
                current_size += amount
                if amount > 0:
                    start_value += amount * price
                else:
                    sold_value += price * (-amount)
        
        curr_value = self.price * current_size
        
        if self.position_type == 'long':
            return curr_value - start_value
        elif self.position_type == 'short':
            return start_value - curr_value
        else:
            raise RuntimeError
    
    def isLong(self):
        return self.position_type == 'long'
    
    def isShort(self):
        return self.position_type == 'short'

class EmptyPosition(Position):
    def __init__(self, candle_feed, currency='USD', evaluate_at='low',
                 position_type='long'):
        super().__init__(candle_feed, currency=currency,
                         evaluate_at=evaluate_at,
                         position_type=position_type)
