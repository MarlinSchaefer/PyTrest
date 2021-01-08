import numpy as np
import datetime
import warnings
from ..currency import Money

class Candle(object):
    def __init__(self, data=None, currency=None, timestamp=None,
                 names=None):
        self.required_keys = ['open', 'close', 'high', 'low', 'volume']
        self.names = {'open': 'Open',
                      'close': 'Close',
                      'high': 'High',
                      'low': 'Low',
                      'volume': 'Volume'}
        if names is None:
            names = {}
        self.names.update(names)
        
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
                warnings.warn(msg, RuntimeWarning)
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
    
    def get_by_name(self, name):
        return self.get(self.names[name])
    
    def convert(self, currency):
        data = {}
        money_keys = [self.names[key] for key in ['open', 'close',
                                                  'high', 'low']]
        for key, val in self.data.items():
            if key in money_keys:
                if isinstance(val, Money):
                    data[key] = val.convert(currency, date=self.timestamp)
                else:
                    tmp = Money(val, currency=self.currency)
                    data[key] = tmp.convert(currency, date=self.timestamp)
            else:
                data[key] = val
        ret = Candle(data=data, currency=currency,
                     timestamp=self.timestamp)
        ret.names = self.names
        return ret
    
    def intersecting_keys(self, other):
        if not isinstance(other, type(self)):
            return
        self_keys = list(self.keys())
        other_keys = list(other.keys())
        for key in self.required_keys:
            self_keys.remove(self.names[key])
            other_keys.remove(other.names[key])
        
        return list(set(self_keys).intersection(set(other_keys)))
    
    def as_dict(self):
        name_keys = []
        name_vals = []
        for key, val in self.names.items():
            name_keys.append(key)
            name_vals.append(val)
        attrs = {'required_keys': np.array(self.required_keys, dtype='S'),
                 'names_keys': np.array(name_keys, dtype='S'),
                 'names_vals': np.array(name_vals, dtype='S'),
                 'timestamp': self.timestamp,
                 'currency': self.currency
                }
        ret = {}
        ret['attrs'] = attrs
        ret['data'] = self.data
        return ret
    
    #All math operations
    def binary_operator(self, other, function_name):
        if isinstance(other, type(self)):
            data = {}
            for key in self.required_keys:
                func = getattr(self.get_by_name(key), function_name)
                data[self.names[key]] = func(other.get_by_name(key))
            
            for key in self.intersecting_keys(other):
                func = getattr(self.get(key), function_name)
                data[key] = func(other.get(key))
            
            return self.__class__(data=data, currency=self.currency,
                                  timestamp=self.timestamp,
                                  names=self.names)
        else:
            data = {}
            for key in self.keys():
                func = getattr(self.get(key), function_name)
                data[key] = func(other)
            
            return self.__class__(data=data, currency=self.currency,
                                  timestamp=self.timestamp,
                                  names=self.names)
    
    def unary_operator(self, function_name):
        data = {}
        for key in self.keys():
            func = getattr(self.get(key), function_name)
            data[key] = func()
        return self.__class__(data=data, currency=self.currency,
                              timestamp=self.timestamp,
                              names=self.names)
    
    def __add__(self, other):
        return self.binary_operator(other, '__add__')
    
    def __neg__(self):
        return self.unary_operator('__neg__')
        #data = {}
        #for key, val in self.data.items():
            #data[key] = -val
        #return self.__class__(data=data, currency=self.currency,
                              #timestamp=self.timestamp,
                              #names=self.names)
    
    def __sub__(self, other):
        return self.binary_operator(other, '__sub__')
    
    def __mul__(self, other):
        return self.binary_operator(other, '__mul__')
    
    def __truediv__(self, other):
        return self.binary_operator(other, '__truediv__')
    
    def __rtruediv__(self, other):
        if isinstance(other, (float, int, Money)):
            data = {}
            for key in self.keys():
                data[key] = other / self.get(key)
            return self.__class__(data=data, currency=self.currency,
                                  timestamp=self.timestamp,
                                  names=self.names)
    
    def __abs__(self):
        return self.unary_operator('__abs__')
        #data = {}
        #for key in self.keys():
            #data[key] = abs(self.get(key))
        #return self.__class__(data=data, currency=self.currency,
                              #timestamp=self.timestamp,
                              #names=self.names)
    
    def __and__(self, other):
        return self.binary_operator(other, '__and__')
    
    def __or__(self, other):
        return self.binary_operator(other, '__or__')
    
    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.data == other.data
        elif isinstance(other, dict):
            return self.data == other
        else:
            return False
    
    def __ge__(self, other):
        return self.binary_operator(other, '__ge__')
    
    def __gt__(self, other):
        return self.binary_operator(other, '__gt__')
    
    def __le__(self, other):
        return self.binary_operator(other, '__le__')
    
    def __lt__(self, other):
        return self.binary_operator(other, '__lt__')
