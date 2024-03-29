from PyTrest.types import DateSeries, Candle
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import datetime
import yfinance as yf
import numpy as np
import pandas
import os
import requests


class SubFeed(DateSeries):
    def __init__(self, candle_attribute='open', **kwargs):
        super().__init__(**kwargs)
        self.candle_attribute = candle_attribute
        self.handler.listen('insert_value', self.insert_value_action)
    
    def insert_value_action(self, event):
        if event.emitter is self.parent:
            dateindex = event.args[1]
            if 'value' in kwargs:
                candle = kwargs['value']
            else:
                candle = args[2]
            print(f"SubFeed for {self.parent.name}.{self.candle_attribute} received valid insert_value")
            self.insert_value(dateindex,
                              value=getattr(candle, self.candle_attribute))

class CandleFeed(DateSeries):
    def __init__(self, name='N/A', currency='USD', data=None, index=None,
                 datetime_format='%d.%m.%Y %H:%M:%S'):
        super().__init__(data=data, index=index,
                         datetime_format=datetime_format)
        self.name = name
        self.currency = currency
    
    def __hash__(self):
        return hash(self.name)
    
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
    
    def value_by_name(self, name):
        return self.value.get_by_name(name)
    
    @property
    def open(self):
        data = []
        for candle in self.data:
            data.append(candle.open)
        return SubFeed(data=data, index=self.index,
                       datetime_format=self.datetime_format,
                       parent=self, candle_attribute='open')
    
    @property
    def close(self):
        data = []
        for candle in self.data:
            data.append(candle.close)
        return SubFeed(data=data, index=self.index,
                       datetime_format=self.datetime_format,
                       parent=self, candle_attribute='close')
    
    @property
    def high(self):
        data = []
        for candle in self.data:
            data.append(candle.high)
        return SubFeed(data=data, index=self.index,
                       datetime_format=self.datetime_format,
                       parent=self, candle_attribute='high')
    
    @property
    def low(self):
        data = []
        for candle in self.data:
            data.append(candle.low)
        return SubFeed(data=data, index=self.index,
                       datetime_format=self.datetime_format,
                       parent=self, candle_attribute='low')
    
    @property
    def volume(self):
        data = []
        for candle in self.data:
            data.append(candle.volume)
        return SubFeed(data=data, index=self.index,
                       datetime_format=self.datetime_format,
                       parent=self, candle_attribute='volume')
    vol = volume
    
    def to_dataframe(self):
        length = 0
        data = {}
        for candle in self.data:
            for key, val in candle.data.items():
                if key not in data:
                    data[key] = [np.nan for _ in range(length)]
                data[key].append(float(val))
            length += 1
        df = pandas.DataFrame(data=data, index=self.index)
        return df
    
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
    
    def plot(self, fig=None, ax=None, **kwargs):
        if fig is None:
            if ax is None:
                fig, ax = plt.subplots()
            else:
                fig = plt.figure()
                fig.add_axes(ax)
        else:
            if ax is None:
                ax = fig.add_subplot(111)
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
            ax.add_patch(Rectangle((date-width/2, float(candle.open)),
                                   width,
                                   height,
                                   color=color))
        return fig, ax
    
    def save(self, file_path, overwrite=True):
        if os.path.isfile(file_path) and not overwrite:
            raise IOError(f'File {file_path} already exists. Use overwrite to overwrite it.')
        with pandas.HDFStore(file_path, 'w') as store:
            store['df'] = self.to_dataframe()
            aux_info = pandas.DataFrame({'name': [self.name],
                                         'currency': [self.currency],
                                         'datetime_format': [self.datetime_format]})
            store['aux_info'] = aux_info
    
    @classmethod
    def load(cls, file_path):
        with pandas.HDFStore(file_path, 'r') as store:
            df = store['df']
            aux_info = store['aux_info']
            name = aux_info['name'].iloc[0]
            currency = aux_info['currency'].iloc[0]
            datetime_format = aux_info['datetime_format'].iloc[0]
        return cls.from_dataframe(df, name=name, currency=currency,
                                  datetime_format=datetime_format)
    
    from_save = load

    def __getitem__(self, index):
        ds = super().__getitem__(index)
        if isinstance(ds, DateSeries):
            return CandleFeed(data=ds.data, index=ds.index, name=self.name,
                              datetime_format=ds.datetime_format,
                              currency=self.currency)
        else:
            return ds


class YahooFeed(CandleFeed):
    def __init__(self, ticker, datetime_format='%d.%m.%Y %H:%M:%S',
                 **kwargs):
        ticker_name = str(ticker)
        ticker = yf.Ticker(ticker)
        url = f'https://query2.finance.yahoo.com/v8/finance/chart/{ticker_name}'
        header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"}
        params = {}
        params['range'] = "30d"
        params['interval'] = "1d"
        params['includePrePost'] = False
        params['events'] = 'div,splits'
        try:
            response = requests.get(url=url,
                                    params=params,
                                    headers=header)

            data = response.json()["chart"]["result"][0]
            currency = data["meta"]["currency"]
        except Exception:
            currency = ticker.info['currency']
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
        super().__init__(name=ticker_name, currency=currency, data=data,
                         index=index, datetime_format=datetime_format)
    
    def __str__(self):
        return f"YahooFeed({self.name}, start={self.min_dateindex}, end={self.max_dateindex})"
    
    def __repr__(self):
        return f"YahooFeed({self.name}, start={self.min_dateindex}, end={self.max_dateindex})"


class YahooFeedFast(CandleFeed):
    def __init__(self, ticker, period='1y', interval='1d'):
        url = f'https://query2.finance.yahoo.com/v8/finance/chart/{ticker}'

        header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"}

        params = {}
        params['range'] = period.lower()
        params['interval'] = interval.lower()
        params['includePrePost'] = False
        params['events'] = 'div,splits'

        response = requests.get(url=url,
                                params=params,
                                headers=header)

        data = response.json()["chart"]["result"][0]
        currency = data["meta"]["currency"]

        times = data["timestamp"]
        prices = data["indicators"]["quote"][0]
        payload = []
        index = []
        for t, h, l, o, c, v in zip(times, prices["high"], prices["low"],
                                    prices["open"], prices["close"],
                                    prices['volume']):
            t = datetime.datetime.fromtimestamp(t)
            candle = Candle(data={"High": h,
                                  "Low": l,
                                  "Open": o,
                                  "Close": c,
                                  "Volume": v},
                            currency=currency,
                            timestamp=t)
            payload.append(candle)
            index.append(t)
        super().__init__(name=ticker, currency=currency, data=payload,
                         index=index)
