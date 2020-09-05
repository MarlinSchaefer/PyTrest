from PyTrest.currency import Money
from PyTrest.feed import CandleFeed

class BaseConstraint(object):
    def __init__(self, candle_feed=None):
        assert isinstance(candle_feed, (CandleFeed, type(None)))
        self.candle_feed = candle_feed
    
    def check(self, dateindex):
        raise NotImplementedError

class StopConstraint(BaseConstraint):
    def __init__(self, candle_feed, stop_price, direction='rising'):
        super().__init__(candle_feed=candle_feed)
        assert isinstance(stop_price, (int, float, Money))
        self.stop_price = stop_price
        self.direction = direction
        self.stop_triggered = False
        self.trigger_date = None
    
    @property
    def direction(self):
        return self._direction
    
    @direction.setter
    def direction(self, direction):
        if not isinstance(direction, str):
            raise TypeError
        elif direction.lower() not in ['rising', 'falling']:
            raise ValueError
        else:
            self._direction = direction.lower()
    
    def check(self, dateindex):
        if self.stop_triggered:
            if self.trigger_date < dateindex:
                return True
            else:
                return False
        else:
            candle = self.candle_feed[dateindex]
            if self.direction == 'rising':
                if candle.high >= self.stop_price:
                    self.stop_triggered = True
                    self.trigger_date = dateindex
                    return True
                else:
                    return False
            elif self.direction == 'falling':
                if candle.low <= self.stop_price:
                    self.stop_triggered = True
                    self.trigger_date = dateindex
                    return True
                else:
                    return False
            else:
                raise RuntimeError

class LimitConstraint(StopConstraint):
    def __init__(self, candle_feed, limit_price, direction='rising'):
        assert isinstance(candle_feed, CandleFeed)
        self.candle_feed = candle_feed
        assert isinstance(limit_price, (int, float, Money))
        self.limit_price = limit_price
        self.direction = direction
    
    def check(self, dateindex):
        candle = self.candle_feed[dateindex]
        if self.direction == 'rising':
            return self.limit_price >= candle.low
        elif self.direction == 'falling':
            return self.limit_price <= candle.high

class CancelConstraint(BaseConstraint):
    def check(self, dateindex):
        return False
