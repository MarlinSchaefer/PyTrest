import datetime
import yfinance as yf
import numpy as np
import json
import os
import warnings

DEFAULT_CONV_TYPE = 'online'
CONV_WARN = True

class ConvType(object):
    cache_location = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'cache_file.json')
    default_cache_interval = datetime.timedelta(minutes=30)
    datetime_format = '%d.%m.%Y %H:%M:%S'
    def __init__(self):
        self.default_type = DEFAULT_CONV_TYPE
        self.load_cache()
    
    def load_cache(self):
        from ..types import DateSeries
        self.cache = {}
        try:
            with open(self.cache_location, 'r') as fp:
                tmp = json.load(fp)
            tmp = tmp.get('content', {})
            for old, dic in tmp.items():
                self.cache[old] = {}
                for new, dsdic in dic.items():
                    ds = DateSeries.from_dict(dsdic)
                    if 'updated' in dsdic:
                        ds.updated = datetime.datetime.strptime(dsdic['updated'], ds.datetime_format)
                    self.cache[old][new] = ds
        except:
            pass
    
    def write_cache(self, force=False, cache_interval=None):
        if not force:
            with open(self.cache_location) as fp:
                tmp = json.load(fp)
            last_written = tmp.get('last_written', None)
            if last_written is not None:
                last_written = datetime.datetime.strptime(last_written, self.datetime_format)
                
                if cache_interval is None:
                    cache_interval = self.default_cache_interval
                
                if abs(datetime.datetime.now() - last_written) < cache_interval:
                    return
        to_write = {}
        for old, dic in self.cache.items():
            to_write[old] = {}
            for new, ds in dic.items():
                to_write[old][new] = ds.as_dict()
                if hasattr(ds, 'updated'):
                    to_write[old][new]['updated'] = ds.updated.strftime(self.datetime_format)
        to_write = {'last_written': datetime.datetime.now().strftime(self.datetime_format),
                    'content': to_write}
        with open(self.cache_location, 'w') as fp:
            json.dump(to_write, fp, indent=4)
    
    def convert(self, mon, new_curr, conv_type=None, ratio=None, date=None):
        if new_curr == mon.currency:
            return mon
        if conv_type is None:
            conv_type = self.default_type
        if conv_type == 'online':
            return self.convert_online(mon, new_curr, date=date)
        elif conv_type == 'cached':
            return self.convert_cached(mon, new_curr, date=date)
        elif conv_type == 'fixed':
            if ratio is None:
                ratio = 1
                if CONV_WARN:
                    warnings.warn(f'Missing coversion factor for fixed conversion. Using 1 as conversion factor.')
            return self.convert_fixed(mon, new_curr, ratio, date=date)
    
    def convert_online(self, mon, new_curr, date=None):
        if date is None:
            date = datetime.datetime.now()
        
        cached = self.check_cached(mon.currency, new_curr, date=date)
        if cached:
            return self.convert_cached(mon, new_curr, date=date)
        
        start_date = (date - datetime.timedelta(days=3)).date()
        end_date = date.date() + datetime.timedelta(days=3)
        if mon.currency == 'USD':
            ticker = new_curr.upper() + '=X'
        else:
            ticker = mon.currency + new_curr.upper() + '=X'
        
        try:
            data = yf.Ticker(ticker).history(start=start_date,
                                             end=end_date,
                                             interval='1m')
        except:
            data = yf.Ticker(ticker).history(start=start_date,
                                             end=end_date,
                                             interval='1d')
        
        self.cache_data(data, mon.currency, new_curr, date)
        
        if len(data) == 0:
            return self.convert_cached(mon, new_curr, date=date)
        
        idx = np.argmin(np.abs([pt.to_pydatetime().astimezone().replace(tzinfo=None) - date for pt in data.index]))
        
        conversion_factor = data.iloc[idx]['Low']
        return Money(mon.amount * conversion_factor, currency=new_curr)
    
    def check_cached(self, old, new_curr, date=None):
        if not old in self.cache:
            return False
        if not new_curr in self.cache[old]:
            return False
        data = self.cache[old][new_curr]
        now = datetime.datetime.now()
        if date is None:
            date = now
        diff = [abs(pt - date) for pt in data.index]
        idx = np.argmin(diff)
        if diff[idx] < datetime.timedelta(seconds=60):
            return True
        elif diff[idx] < datetime.timedelta(days=1):
            if date - now < datetime.timedelta(days=30):
                if hasattr(data, 'updated') and abs(data.updated - datetime.datetime.now()) < datetime.timedelta(seconds=60):
                    return True
                return False
            else:
                return True
        else:
            return False
    
    def cache_data(self, data, old_curr, new_curr, date):
        from ..types import DateSeries
        if not old_curr in self.cache:
            self.cache[old_curr] = {}
        if not new_curr in self.cache[old_curr]:
            self.cache[old_curr][new_curr] = DateSeries()
        
        for i in range(len(data)):
            cd = data.index[i].to_pydatetime().astimezone().replace(tzinfo=None)
            if cd not in self.cache[old_curr][new_curr].index:
                self.cache[old_curr][new_curr].insert_value(cd, value=data.iloc[i]['Low'])
        
        self.cache[old_curr][new_curr].updated = date
        
        self.write_cache()
    
    def convert_cached(self, mon, new_curr, date=None):
        old = mon.currency
        if old not in self.cache:
            if CONV_WARN:
                warnings.warn(f'Did not find cached value to convert {old} to {new_curr}. Using conversion factor of 1.')
            return self.convert_fixed(mon, new_curr, 1, date=date)
        if new_curr not in self.cache[old]:
            if CONV_WARN:
                warnings.warn(f'Did not find cached value to convert {old} to {new_curr}. Using conversion factor of 1.')
            return self.convert_fixed(mon, new_curr, 1, date=date)
        
        if date is None:
            date = datetime.datetime.now()
        data = self.cache[old][new_curr]
        
        diff = [abs(pt - date) for pt in data.index]
        idx = np.argmin(diff)
        
        if diff[idx] > datetime.timedelta(days=3) and CONV_WARN:
            warnings.warn(f'Using data that is more than 3 days away from {date}.')
        
        conv_fac = self.cache[old][new_curr].data[idx]
        
        return Money(mon.amount * conv_fac, currency=new_curr)
    
    def convert_fixed(self, mon, new_curr, ratio, date=None):
        return Money(mon.amount * ratio, currency=new_curr)
    
    def update_cache(self, old, new, date=None):
        if date is None:
            date = datetime.datetime.now()
        
        cached = self.check_cached(old, new, date=date)
        if cached:
            return
        
        start_date = (date - datetime.timedelta(days=3)).date()
        end_date = date.date() + datetime.timedelta(days=3)
        if old == 'USD':
            ticker = new.upper() + '=X'
        else:
            ticker = old + new.upper() + '=X'
        
        try:
            data = yf.Ticker(ticker).history(start=start_date,
                                             end=end_date,
                                             interval='1m')
        except:
            data = yf.Ticker(ticker).history(start=start_date,
                                             end=end_date,
                                             interval='1d')
        
        self.cache_data(data, old, new, date)
        self.write_cache(force=True)
    
    def download_cache(self, old, new, start_date=None,
                       end_date=None, period=None):
        old = old.upper()
        new = new.upper()
        if old.upper() == 'USD':
            ticker = new.upper() + '=X'
        else:
            ticker = old.upper() + new.upper() + '=X'
        
        data = yf.Ticker(ticker).history(start=start_date, end=end_date,
                                         period=period)
        
        date = None
        if old in self.cache:
            if new in self.cache[old]:
                if hasattr(self.cache[old][new], 'updated'):
                    date = self.cache[old][new].updated
        if date is None:
            data.index.max().to_pydatetime()
        
        self.cache_data(data, old, new, date)
        self.write_cache(force=True)
        
DEFAULT_CONV = ConvType()

def set_conversion_type(new_type):
    global DEFAULT_CONV_TYPE
    global DEFAULT_CONV
    if isinstance(new_type, int):
        type_conversion = {0: 'online',
                           1: 'cached',
                           2: 'fixed'}
        new_type = type_conversion[new_type]
    if not isinstance(new_type, str):
        raise TypeError('New conversion type must be either string or int.')
    
    DEFAULT_CONV.default_type = new_type
    DEFAULT_CONV_TYPE = new_type

def update_cache(old, new, date=None):
    global DEFAULT_CONV
    DEFAULT_CONV.update_cache(old, new, date=date)

def disable_conversion_warnings():
    global CONV_WARN
    CONV_WARN = False

def enable_conversion_warnings():
    global CONV_WARN
    CONV_WARN = True

def toggle_conversion_warnings():
    global CONV_WARN
    CONV_WARN = not CONV_WARN

class Money(object):
    converter = DEFAULT_CONV
    def __init__(self, amount, currency='USD', conversion_date=None):
        self.currency = currency.upper()
        self.conversion_date = conversion_date
        self.amount = amount
    
    @property
    def amount(self):
        return self._amount
    
    @amount.setter
    def amount(self, amount):
        if amount is None:
            self._amount = 0.
        elif isinstance(amount, (int, float)):
            self._amount = float(amount)
        elif isinstance(amount, type(self)):
            self._amount = amount.amount
            self.currency = amount.currency
            self.conversion_date = amount.conversion_date
        else:
            raise TypeError
    
    def set_conversion_date(self, date):
        self.conversion_date = date
    
    def convert(self, currency, ratio=None, date=None):
        return self.converter.convert(self, currency, ratio=ratio, date=date)
    
    def as_own_currency(self, other):
        if other.currency == self.currency:
            return other
        else:
            return other.convert(self.currency,
                                 date=self.conversion_date)
    
    def copy_new_amount(self, amount):
        return Money(amount,
                     currency=self.currency,
                     conversion_date=self.conversion_date)
    
    def __add__(self, other):
        if isinstance(other, type(self)):
            o = self.as_own_currency(other)
            return self.copy_new_amount(self.amount + o.amount)
        elif isinstance(other, float) or isinstance(other, int):
            return self.copy_new_amount(self.amount + other)
        else:
            msg = f'Cannot add instance of type {type(other)} to'
            msg += f'instance of type {type(self)}.'
            raise TypeError(msg)
    
    def isnum(self, inp):
        return isinstance(inp, float) or isinstance(inp, int)
    
    def __radd__(self, other):
        return self.__add__(other)
    
    def __neg__(self):
        return self.copy_new_amount(-self.amount)
    
    def __sub__(self, other):
        return self.__add__(-other)
    
    def __rsub__(self, other):
        tmp = -self
        return tmp.__add__(other)
    
    def __mul__(self, other):
        if self.isnum(other):
            return self.copy_new_amount(self.amount * other)
        else:
            msg = 'Can multiply money only by a number. Got type '
            msg += f'{type(other)} instead.'
            raise TypeError(msg)
    
    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __truediv__(self, other):
        if self.isnum(other):
            return self.copy_new_amount(self.amount / other)
        elif isinstance(other, type(self)):
            o = self.as_own_currency(other)
            return self.copy_new_amount(self.amount / o.amount)
        else:
            msg = 'Can divide money only by a number or Money. Got'
            msg += f'{type(other)} instead.'
            raise TypeError(msg)
    
    def __rtruediv__(self, other):
        if isinstance(other, type(self)):
            o = self.as_own_currency(other)
            return self.copy_new_amount(o.amount / self.amount)
        else:
            msg = 'If the nominator is a Money instance the numerator '
            msg += f'has to also be a Money instance. Got {type(other)}'
            msg += 'instead.'
            raise TypeError(msg)
    
    def __lt__(self, other):
        if self.isnum(other):
            return self.amount < other
        elif isinstance(other, type(self)):
            o = self.as_own_currency(other)
            return self.amount < o.amount
        elif other is None:
            return False
        else:
            msg = 'Can compare Money only to numbers or other instances'
            msg += f' of Money. Got {type(other)} instead.'
            raise TypeError(msg)
    
    def __le__(self, other):
        if self.isnum(other):
            return self.amount <= other
        elif isinstance(other, type(self)):
            o = self.as_own_currency(other)
            return self.amount <= o.amount
        elif other is None:
            return False
        else:
            msg = 'Can compare Money only to numbers or other instances'
            msg += f' of Money. Got {type(other)} instead.'
            raise TypeError(msg)
    
    def __gt__(self, other):
        if self.isnum(other):
            return self.amount > other
        elif isinstance(other, type(self)):
            o = self.as_own_currency(other)
            return self.amount > o.amount
        elif other is None:
            return False
        else:
            msg = 'Can compare Money only to numbers or other instances'
            msg += f' of Money. Got {type(other)} instead.'
            raise TypeError(msg)
    
    def __ge__(self, other):
        if self.isnum(other):
            return self.amount >= other
        elif isinstance(other, type(self)):
            o = self.as_own_currency(other)
            return self.amount >= o.amount
        elif other is None:
            return False
        else:
            msg = 'Can compare Money only to numbers or other instances'
            msg += f' of Money. Got {type(other)} instead.'
            raise TypeError(msg)
    
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        else:
            o = self.as_own_currency(other)
            return self.amount == o.amount
    
    def __ne__(self, other):
        if not isinstance(other, type(self)):
            return True
        else:
            o = self.as_own_currency(other)
            return self.amount != o.amount
    
    def __abs__(self):
        return self.copy_new_amount(abs(self.amount))
    
    def __str__(self):
        return str(self.amount) + ' ' + self.currency.upper()
    
    def __repr__(self):
        ret = 'Money(' + str(self.amount) + ', currency='
        ret += self.currency.upper() + ', conversion_date='
        ret += str(self.conversion_date) + ')'
        return ret
    
    def __float__(self):
        return float(self.amount)
    
    def __int__(self):
        return int(self.amount)
    
    pass
