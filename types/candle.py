import numpy as np
import datetime
import warnings
from PyTrest.currency import Money

class Candle(object):
    def __init__(self, data=None, currency=None, timestamp=None,
                 names=None):
        if names is None:
            self.names = {'open': 'Open',
                        'close': 'Close',
                        'high': 'High',
                        'low': 'Low',
                        'volume': 'Volume'}
        else:
            for key in ['open', 'close', 'high', 'low', 'volume']:
                if key not in names:
                    raise ValueError
            self.names = names
        self.timestamp = timestamp
        self.currency = currency
        self.data = data
    
    def keys(self):
        return self.data.keys()
    
    def in_price_range(self, value):
        return self.low < value < self.high
    
    def __contains__(self, item):
        if isinstance(item, str):
            return item in self.data
        elif isinstance(item, (float, int, Money)):
            return self.in_price_range(item)
        else:
            return item in list(self.data.values())
    
    def set_timestamp(self, timestamp=None):
        if timestamp is None:
            timestamp = datetime.datetime.now()
        if not isinstance(timestamp, datetime.datetime):
            msg = 'timestamp must be either None or of type datetime.'
            raise TypeError(msg)
        self.timestamp = timestamp
    
    def set_name(self, key, new_name=None):
        if new_name is None:
            return
        self.names[key] = str(new_name)
    
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, data):
        if data is None:
            self._data = {}
        elif isinstance(data, dict):
            missing_data = []
            for val in self.names.values():
                if val not in data:
                    missing_data.append(val)
                    data[val] = np.nan
            if len(missing_data) > 0:
                msg = 'Data is missing required keys {}.'.format(missing_data)
                warning.warn(msg, RuntimeWarning)
            self._data = data
        else:
            raise TypeError('Unrecognized type.')
    
    @property
    def open(self):
        return self.get(self.names['open'], as_currency=True)
    
    @open.setter
    def open(self, open):
        self.data[self.names['open']] = open
    
    @property
    def close(self):
        return self.get(self.names['close'], as_currency=True)
    
    @close.setter
    def close(self, close):
        self.data[self.names['close']] = close
    
    @property
    def high(self):
        return self.get(self.names['high'], as_currency=True)
    
    @high.setter
    def high(self, high):
        self.data[self.names['high']] = high
    
    @property
    def low(self):
        return self.get(self.names['low'], as_currency=True)
    
    @low.setter
    def low(self, low):
        self.data[self.names['low']] = low
    
    @property
    def volume(self):
        return self.get(self.names['volume'], as_currency=False)
    
    @volume.setter
    def volume(self, volume):
        self.data[self.names['volume']] = volume
    vol = volume
    
    def get(self, k, d=None, as_currency=False):
        if self.currency is not None and as_currency:
            if k in list(self.names.values()) and not k == self.names['volume']:
                return Money(self.data.get(k, d),
                            currency=self.currency,
                            conversion_date=self.timestamp)
        return self.data.get(k, d)
    
    def convert(self, currency):
        data = {}
        for key, val in self.data.items():
            if isinstance(val, Money):
                data[key] = val.convert(currency, date=self.timestamp)
            else:
                data[key] = val
        ret = Candle(data=data, currency=currency,
                     timestamp=self.timestamp)
        ret.names = self.names
        return ret
    
    #All math operations
    def __add__(self, other):
        if isinstance(other, (dict, type(self))):
            assert list(other.keys()) == list(self.keys())
            data = {}
            for key in self.keys():
                data[key] = self.get(key) + other.get(key)
            
            return Candle(data=data, currency=self.currency)
        else:
            raise TypeError()
    
    def __neg__(self):
        data = {}
        for key, val in self.data.items():
            data[key] = -val
        return self.__class__(data=data, currency=self.currency,
                              timestamp=self.timestamp)
    
    def __sub__(self, other):
        return self.__add__(-other)
