from PyTrest.types import DateSeries, Candle
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import datetime
import yfinance as yf

class CandleFeed(DateSeries):
    def __init__(self, name='N/A', currency='USD', data=None, index=None,
                 datetime_format='%d.%m.%Y %H:%M:%S'):
        super().__init__(data=data, index=index,
                       datetime_format=datetime_format)
        self.name = name
        self.currency = currency
    
    def add_candle(self, dateindex, candle, names=None):
        if isinstance(candle, Candle):
            if candle.currency != self.currency:
                candle = candle.convert(self.currency)
            if candle.timestamp is None:
                candle.timestamp = dateindex
            elif candle.timestamp != dateindex:
                candle.timestamp = dateindex
            self.insert_value(dateindex, value=candle)
        else:
            candle = Candle(data=candle, currency=self.currency,
                            timestamp=dateindex, names=names)
            self.insert_value(dateindex, value=candle)
    
    @property
    def open(self):
        data = []
        for candle in self.data:
            data.append(candle.open)
        return DateSeries(data=data, index=self.index,
                          datetime_format=self.datetime_format)
    
    @property
    def close(self):
        data = []
        for candle in self.data:
            data.append(candle.close)
        return DateSeries(data=data, index=self.index,
                          datetime_format=self.datetime_format)
    
    @property
    def high(self):
        data = []
        for candle in self.data:
            data.append(candle.high)
        return DateSeries(data=data, index=self.index,
                          datetime_format=self.datetime_format)
    
    @property
    def low(self):
        data = []
        for candle in self.data:
            data.append(candle.low)
        return DateSeries(data=data, index=self.index,
                          datetime_format=self.datetime_format)
    
    @property
    def volume(self):
        data = []
        for candle in self.data:
            data.append(candle.volume)
        return DateSeries(data=data, index=self.index,
                          datetime_format=self.datetime_format)
    vol = volume
    
    @classmethod
    def from_dataframe(cls, dataframe, name='N/A', currency='USD',
                       datetime_format='%d.%m.%Y %H:%M:%S', names=None):
        if names is None:
            names = Candle().names
        
        index = [date.to_pydatetime() for date in dataframe.index]
        data = []
        for i in range(len(dataframe)):
            data.append(Candle(data=dict(dataframe.iloc[i]),
                               currency=currency,
                               timestamp=index[i],
                               names=names))
        return CandleFeed(name=name, currency=currency, data=data,
                          index=index, datetime_format=datetime_format)
    
    def plot(self):
        fig, ax = plt.subplots()
        width = datetime.timedelta(days=0.5)
        for date, candle in zip(self.index, self.data):
            if candle.open < candle.close:
                color = 'green'
            else:
                color = 'red'
            ax.plot([date, date],
                    [float(candle.low), float(candle.high)],
                    color=color)
            height = float(candle.close - candle.open)
            ax.add_patch(Rectangle((date-width/2, float(candle.close)),
                                   width,
                                   height,
                                   color=color))
        plt.show()

class YahooFeed(CandleFeed):
    def __init__(self, ticker, currency='USD',
                 datetime_format='%d.%m.%Y %H:%M:%S', **kwargs):
        ticker = yf.Ticker(ticker)
        if 'period' not in kwargs:
            kwargs['period'] = 'max'
        dataframe = ticker.history(**kwargs)
        
        names = Candle().names
        index = [date.to_pydatetime() for date in dataframe.index]
        data = []
        for i in range(len(dataframe)):
            data.append(Candle(data=dict(dataframe.iloc[i]),
                               currency=currency,
                               timestamp=index[i],
                               names=names))
        super().__init__(name=str(ticker), currency=currency, data=data,
                          index=index, datetime_format=datetime_format)
