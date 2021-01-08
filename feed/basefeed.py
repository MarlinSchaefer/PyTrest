from PyTrest.types import DateSeries, Candle
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import datetime
import yfinance as yf
import h5py
import numpy as np

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
    
    def save(self, file_path):
        with h5py.File(file_path, 'w') as fp:
            fp.attrs['name'] = self.name
            fp.attrs['currency'] = self.currency
            fp.attrs['datetime_format'] = self.datetime_format
            dates = [pt.strftime(self.datetime_format) for pt in self.index]
            fp.create_dataset('index', data=np.array(dates, dtype='S'))
            data = fp.create_group('data')
            for date in self.index:
                date_gr = data.create_group(date.strftime(self.datetime_format))
                candle = self[date]
                store_dict = candle.as_dict()
                for key, val in store_dict['attrs'].items():
                    if key == 'timestamp':
                        if val is None:
                            date_gr.attrs[key] = 'None'
                        else:
                            date_gr.attrs[key] = val.strftime(self.datetime_format)
                    else:
                        date_gr.attrs[key] = val
                for key, val in store_dict['data'].items():
                    curr_set = date_gr.create_dataset(key, data=np.float(val))
    
    @classmethod
    def from_save(cls, file_path):
        with h5py.File(file_path, 'r') as fp:
            name = fp.attrs['name']
            cur = fp.attrs['currency']
            df = fp.attrs['datetime_format']
            tmp = fp['index'][()].astype(str)
            index = [datetime.datetime.strptime(pt, df) for pt in tmp]
            data = []
            for datestr in tmp:
                candle_data = fp['data'][datestr]
                kwargs = {}
                for key, val in dict(candle_data.attrs).items():
                    key = str(key)
                    if key == 'names_keys':
                        names_keys = val
                    elif key == 'names_vals':
                        names_vals = val
                    elif key == 'required_keys':
                        continue
                    elif key == 'timestamp':
                        if str(val) == 'None':
                            kwargs[key] = None
                        else:
                            kwargs[key] = datetime.datetime.strptime(str(val), df)
                    else:
                        kwargs[key] = val
                kwargs['names'] = {key: val for (key, val) in zip(names_keys, names_vals)}
                    
                candle = {}
                for key in candle_data.keys():
                    candle[key] = candle_data[key][()]
                kwargs['data'] = candle
                data.append(Candle(**kwargs))
            return CandleFeed(name=name,
                              currency=cur,
                              datetime_format=df,
                              index=index,
                              data=data)

class YahooFeed(CandleFeed):
    def __init__(self, ticker, currency='USD',
                 datetime_format='%d.%m.%Y %H:%M:%S', **kwargs):
        ticker_name = str(ticker)
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
        super().__init__(name=ticker_name, currency=currency, data=data,
                          index=index, datetime_format=datetime_format)
    
    #def copy(self):
        #return CandleFeed(name=self.name, currency=self.currency,
                          #data=self.data.copy(), index=self.index.copy(),
                          #datetime_format=self.datetime_format)
