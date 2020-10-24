import datetime
import yfinance as yf
import numpy as np

class Money(object):
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
    
    def convert(self, currency, date=None):
        if currency == self.currency:
            return self
        if date is None:
            if self.conversion_date is None:
                date = datetime.datetime.now()
            else:
                date = self.conversion_date
        
        start_date = (date - datetime.timedelta(days=3)).date()
        end_date = date.date() + datetime.timedelta(days=3)
        if self.currency == 'USD':
            ticker = currency.upper() + '=X'
        else:
            ticker = self.currency + currency.upper() + '=X'
        try:
            data = yf.Ticker(ticker).history(start=start_date,
                                             end=end_date,
                                             interval='1m')
        except:
            data = yf.Ticker(ticker).history(start=start_date,
                                             end=end_date,
                                             interval='1d')
        
        idx = np.argmin(np.abs([pt - date.astimezone(pt.tzinfo) for pt in data.index]))
        
        conversion_factor = data.iloc[idx]['Low']
        return Money(self.amount * conversion_factor, currency=currency)
    
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
