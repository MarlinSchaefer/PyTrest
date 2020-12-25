import warnings
from ..types.dateseries_synced import DateSeries

class EMA(DateSeries):
    def __init__(self, parent, window_size=None, alpha=None, **kwargs):
        if window_size is None and alpha is None:
            msg = 'Either the window size or the alpha-value has to be '
            msg += 'provided for the exponential moving average.'
            raise ValueError(msg)
        elif window_size is not None and alpha is not None:
            msg = 'The alpha may be set directly or indirectly through '
            msg += 'a window size. Both were provided. However, the '
            msg += 'provided value of alpha takes prescedence and will '
            msg += 'be used. (Ignoring window_size)'
            warnings.warn(msg, RuntimeWarning)
            self.alpha = alpha
        elif window_size is not None:
            self.alpha = 2. / (window_size + 1)
        else:
            self.alpha = alpha
        self.inv_alpha = 1 - self.alpha
        
        super().__init__(parent, **kwargs)
        self.handler.listen('insert_value', self.insert_value_action)
        self.handler.listen('__setitem__', self.setitem_action)
        self.compute_from_index(0)
    
    def compute_from_index(self, index):
        if index >= len(self):
            if index >= len(self.parent):
                return
            for i in range(len(self), index+1):
                self.insert_value(self.parent.index[i], value=None)
            
        for i in range(index, len(self.parent)):
            if self.parent.data[i] is None:
                if i < len(self):
                    self[i] = None
                else:
                    self.insert_value(self.parent.index[i], value=None)
            else:
                if i == index:
                    if all([pt is None for pt in self.data]):
                        self[i] = self.parent.data[i]
                        continue
                curr_data = None
                j = 1
                while curr_data is None and j <= i:
                    curr_data = self.data[i-j]
                    j += 1
                if curr_data is None:
                    val = None
                else:
                    val = self.alpha * self.parent.data[i] + self.inv_alpha * curr_data
                curr_dateindex = self.parent.index[i]
                if curr_dateindex in self:
                    self[curr_dateindex] = val
                else:
                    self.insert_value(curr_dateindex, value=val)
                    
    def setitem_action(self, event):
        if event.emitter is self:
            return
        if not self.is_parent(event.emitter):
            return
        dateindex = event.args[1]
        if isinstance(dateindex, slice):
            dateindex = slice.start
            if dateindex is None:
                dateindex = 0
        if isinstance(dateindex, str):
            datetime.datetime.strptime(start, self.parent.datetime_format)
        if isinstance(dateindex, datetime.datetime):
            if dateindex in self.parent.index:
                dateindex = self.parent.index.index(dateindex)
            else:
                raise ValueError('Dateindex {} not in DateSeries.'.format(dateindex))
        if isinstance(dateindex, int):
            self.compute_from_index(dateindex)
        else:
            raise TypeError
    
    def insert_value_action(self, event):
        if event.emitter is self:
            return
        if not self.is_parent(event.emitter):
            return
        dateindex = event.args[1]
        i = self.parent.index.index(dateindex)
        self.compute_from_index(i)
    
    def copy(self):
        return self.__class__(self.parent, window_size=None,
                              alpha=self.alpha, data=self.data.copy(),
                              index=self.index.copy(),
                              datetime_format=self.datetime_format)

class DMA(EMA):
    def __init__(self, base, window_size=None, alpha=None, **kwargs):
        ema = EMA(base, window_size=window_size, alpha=alpha)
        super().__init__(ema, window_size=window_size, alpha=alpha,
                         **kwargs)
