from ..currency import Money
import numpy as np

class BaseConstraint(object):
    def __init__(self):
        return
    
    def check(self, candle):
        raise NotImplementedError
    
    def update(self):
        raise NotImplementedError

class BaseLimit(BaseConstraint):
    def __init__(self, price=None, limit_type='long'):
        self.limit_type = limit_type
        self.price = price
    
    @property
    def limit_type(self):
        return self._limit_type
    
    @limit_type.setter
    def limit_type(self, limit_type):
        if isinstance(limit_type, str):
            limit_type = limit_type.lower()
            if limit_type in ['long', 'short']:
                self._limit_type = limit_type
            else:
                raise ValueError
        else:
            raise TypeError
    
    @property
    def price(self):
        return self._price
    
    @price.setter
    def price(self, price):
        if price is None:
            if self.limit_type == 'long':
                self._price = np.inf
            elif self.limit_type == 'short':
                self._price = -np.inf
        else:
            self._price = Money(price)
    
    def check(self, candle):
        if self.limit_type == 'long':
            return candle.low < self.price
        elif self.limit_type == 'short':
            return candle.high > self.price
    
    def update(self):
        return

class BaseStop(BaseConstraint):
    def __init__(self, price=None, stop_type='long'):
        self.stop_type = stop_type
        self.price = price
    
    @property
    def stop_type(self):
        return self._stop_type
    
    @stop_type.setter
    def stop_type(self, stop_type):
        if isinstance(stop_type, str):
            stop_type = stop_type.lower()
            if stop_type in ['long', 'short']:
                self._stop_type = stop_type
            else:
                raise ValueError
        else:
            raise TypeError
    
    @property
    def price(self):
        return self._price
    
    @price.setter
    def price(self, price):
        if price is None:
            self._price = None
        else:
            self._price = Money(price)
    
    def check(self, candle):
        if self.price is None:
            return True
        else:
            if self.stop_type == 'long':
                return candle.high >= self.price
            elif self.stop_type == 'short':
                return candle.low <= self.price
    
    def update(self):
        return
    
