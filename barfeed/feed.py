import yfinance as yf
from PyTrest.utils import format_datetime
from PyTrest.currency import Money

class BaseBarFeed(object):
    def __init__(self, default_key='Close', currency='USD'):
        self.default_key = default_key
        self.currency = currency.upper()
        return
    
    def price_difference(self, datetime_1, datetime_2, key=None):
        p1 = self.price_at(datetime=datetime_1, key=key)
        p2 = self.price_at(datetime=datetime_2, key=key)
        return p1 - p2
    
    def __getitem__(self, datetime):
        if isinstance(datetime, slice):
            return self.get_slice(self, datetime)
        else:
            return self.get_price(self, datetime)
    
    def get_price(self, datetime=None, key=None):
        """Returns the price at a given datetime.
        
        Arguments
        ---------
        datetime : {datetime object or None, None}
            If set to None the datetime.now() will be used. If no data
            for the current price is available, the most recent historic
            price will be returned.
        key : {str or None, None}
            The key specifies which price of the candle should be used.
            If set to None, the default key will be used.
        
        Returns
        -------
        price : PyTrest.currency.Money
            The price at the given datetime.
        """
        if key is None:
            key = self.default_key
        return Money(self.get_candle(datetime=datetime)[key],
                     currency=self.currency)
    
    def get_candle(self, datetime=None):
        """Returns the candle at a given datetime.
        
        Arguments
        ---------
        datetime : {datetime object or None, None}
            If set to None the datetime.now() will be used. If no data
            for the current candle is available, the most recent
            historic candle will be returned.
        
        Returns
        -------
        candle : pandas.Series
            Returns a pandas Series with at least the keys:
                -'Open'
                -'Close'
                -'High'
                -'Low'
                -'Volume'
            The different keys specify the according prices (as floats).
        """
        raise NotImplementedError()
    
    def get_slice(self, datetime_slice=None, key=None):
        """Returns a set of prices for the given slice.
        
        Arguments
        ---------
        datetime_slice : {slice of datetime or None, None}
            If set to None, the slice `slice(None, None)` will be used.
        
        Returns
        -------
        series : pandas.Series of PyTrest.currency.Money
            Returns a pandas Series of the prices as Money objects.
        """
        if key is None:
            key = self.default_key
        series = self.get_candle_slice(datetime_slice=datetime_slice)[key]
        return series.apply(lambda x: Money(x, currency=self.currency))
    
    def get_candle_slice(self, datetime_slice=None):
        """Returns a slice of candles for a given datetime range.
        
        Arguments
        ---------
        datetime_slice : {slice of datetime or None, None}
            If set to None, the slice `slice(None, None)` will be used.
        
        Returns
        -------
        candle_slice : pandas.DataFrame
            Returns a pandas DataFrame with at least the columns:
                -'Open'
                -'Close'
                -'High'
                -'Low'
                -'Volume'
            The different columns contain the prices at the according
            datetimes (as floats).
        """
        raise NotImplementedError()
    
    def get_date_range(self):
        raise NotImplementedError()
    
    def get_min_date(self):
        raise NotImplementedError()
    
    def get_max_date(self):
        raise NotImplementedError()
    
    def __next__(self):
        pass
    pass

class YahooFeed(BaseBarFeed):
    def __init__(self, ticker):
        self.ticker_symbol = ticker
        self.ticker = yf.Ticker(ticker)
        super().__init__()
