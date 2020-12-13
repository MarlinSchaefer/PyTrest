import datetime as dt
#import PyTrest.barfeed as bf
from PyTrest.barfeed import YahooFeed, BaseBarFeed
from PyTrest.utils import format_datetime

class BasePosition(object):
    def __init__(self, barfeed, size=0):
        if isinstance(barfeed, BaseBarFeed):
            self.barfeed = barfeed
        elif isinstance(barfeed, str):
            self.barfeed = YahooFeed(barfeed)
        else:
            msg = 'The barfeed argument must be either a Barfeed '
            msg += 'instance or a string specifying a ticker symbol. '
            msg += f'Got {type(barfeed)} instead.'
            raise TypeError(msg)
        self.set_size(size)
        self._open = False
        self.open_date = None
        self.close_date = None
    
    def current_price(self, datetime=None, pricing='Close'):
        datetime = format_datetime(datetime)
        ed = datetime
        sd = datetime - dt.timedelta(days=7)
        data = yf.Ticker(self.ticker).history(start=sd, end=ed)
        return data.iloc[-1][pricing]
    
    def current_value(self, datetime=None, pricing='Close'):
        return self.size * self.current_price(datetime=datetime,
                                              pricing=pricing)
    
    @property
    def open_q(self):
        return self._open
    
    def is_open(self):
        return self.open_q
    
    isopen = is_open
    
    def is_closed(self):
        return not self.open_q
    
    isclosed = is_closed
    
    def close_position(self, datetime=None):
        datetime = format_datetime(datetime)
        if self.is_open():
            if self.open_date < datetime:
                if self.close_date is None:
                    self._open = False
                    self.close_date = datetime
                else:
                    msg = 'Cannot close a position that was closed at '
                    msg += 'a different date. Trying to close at'
                    msg += f'{datetime} but position has a registered '
                    msg += f'close date of {self.close_date}.'
                    raise RuntimeError(msg)
            else:
                msg = 'Cannot close a position before it was opened. '
                msg += f'Position opened at {self.open_date}, trying to'
                msg += f' close at {datetime}.'
                raise ValueError(msg)
        else:
            msg = 'Cannot close a position that is not open.'
            raise RuntimeError(msg)
    
    def open_position(self, datetime=None):
        datetime = format_datetime(datetime)
        if self.is_closed():
            if self.open_date is None:
                if self.close_date is None:
                    self._open = True
                    self.open_date = datetime
                else:
                    msg = 'Cannot open a position that was closed at '
                    msg += 'some date.'
                    raise RuntimeError(msg)
            else:
                msg = 'Cannot open a position that was previously '
                msg += 'opened. This position was opened at '
                msg += f'{self.open_date}. Try to create a new position'
                msg += ' and open that new position instead.'
                raise RuntimeError(msg)
        else:
            msg = 'Cannot open a position that is already open.'
            raise RuntimeError(msg)
    
    def base_returns(self, datetime=None):
        datetime = format_datetime(datetime)
        if self.open_date is None:
            msg = 'The position was not opened yet and therefore has no'
            msg += 'returns.'
            raise RuntimeError(msg)
        if datetime < self.open_date:
            msg = f'Position is not yet opened at {datetime}. It is '
            msg += f'only opened at {self.open_date}. Cannot calculate '
            msg += 'returns.'
            raise RuntimeError(msg)
        if self.close_date is not None:
            datetime = min(self.close_date, datetime)
        return datetime
    
    def returns(self, datetime=None):
        msg = 'This function needs to be completed. Please call '
        msg += '`datetime = super().base_returns(datetime)` at the '
        msg += 'start of the implementation.'
        raise NotImplementedError(msg)
    
    def set_size(self, size):
        if size >= 0:
            self.size = size
        else:
            msg = 'The size of a position must be greater or equal to 0.'
            raise ValueError(msg)
    pass

class LongPosition(BasePosition):
    def returns(self, datetime=None):
        datetime = super().base_returns(datetime)
        print(datetime)
