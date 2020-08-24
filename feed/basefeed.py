from PyTrest.types import DateSeries, Candle

class BaseCandleFeed(DateSeries):
    def __init__(self, name='N/A', currency='USD', data=None, index=None,
                 datetime_format='%d.%m.%Y %H:%M:%S'):
        super.__init__(data=data, index=index,
                       datetime_format=datetime_format)
        self.name = name
        self.currency = currency
    
    def add_candle(self, dateindex, candle):
        if isinstance(candle, Candle):
            if candle.currency != self.currency:
                candle = candle.covnert(self.currency)
            if candle.timestamp is None:
                candle.timestamp = dateindex
            elif candle.timestamp != dateindex:
                candle.timestamp = dateindex
            self.insert_value(dateindex, value=candle)
        else:
            candle = Candle(data=candle, currency=self.currency,
                            timestamp=dateindex)
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
    pass
