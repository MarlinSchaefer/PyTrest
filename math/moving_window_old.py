import numpy as np
import warnings
import datetime
from ..types import DateSeries

class NotCalculated(object):
    pass

class MovingWindow(DateSeries):
    def __init__(self, base, window_size=2):
        self.base = base
        self.window_size = window_size
        self._initialized = False
        super().__init__()
        self._initialized = True
        self.last_base = None
        self.check_base()
    
    @property
    def head(self):
        return self.base.head
    
    @head.setter
    def head(self, head):
        if self._initialized:
            msg = 'Cannot set the head of a DateSeries container '
            msg += 'directly. Please set it by setting the head of the '
            msg += 'base DateSeries.'
            warnings.warn(msg, RuntimeWarning)
    
    def check_base(self):
        if not self.last_base == self.base:
            self.last_base = self.base.copy()
            self.data = [NotCalculated() for _ in range(len(self.base))]
            self.index = self.base.index.copy()
    
    def __getitem__(self, dateindex):
        self.check_base()
        init_ret = super().__getitem__(dateindex)
        if isinstance(dateindex, slice):
            not_known = np.where([isinstance(pt, NotCalculated) for pt in init_ret])[0]
            if len(not_known) > 0:
                start, stop, step = self.sanitize_slice(dateindex)
                indices = []
                if isinstance(start, int):
                    if step is None:
                        step = 1
                    indices = list(range(start, stop, step))
                else:
                    curr = min(start, stop)
                    step = abs(step)
                    while curr < max(start, stop):
                        indices.append(curr)
                        curr += step
                for i in range(len(indices)):
                    if i in not_known:
                        init_ret[i] = self.__getitem__(indices[i])
            return init_ret
        else:
            if isinstance(init_ret, NotCalculated):
                if isinstance(dateindex, int):
                    if dateindex > -1 and dateindex - self.window_size + 1 < 0:
                        ret = None
                    elif dateindex < 0 and abs(dateindex - self.window_size + 1) > len(self.base):
                        ret = None
                    else:
                        ret = self.base[dateindex-self.window_size+1:dateindex+1]
                    self.data[dateindex] = ret
                elif isinstance(dateindex, str):
                    dateindex = datetime.datetime.strptime(dateindex, self.datetime_format)
                if isinstance(dateindex, datetime.datetime):
                    idx = np.searchsorted(np.array(self.index), dateindex)
                    if not self.index[idx] == dateindex:
                        msg = 'Index is not contained in the DateSeries.'
                        raise IndexError(msg)
                    if idx > -1 and idx - self.window_size + 1 < 0:
                        ret = None
                    elif idx < 0 and abs(idx - self.window_size + 1) > len(self.base):
                        ret = None
                    else:
                        ret = self.base[idx-self.window_size+1:idx+1]
                    self.data[dateindex] = ret
                return ret
            else:
                return init_ret

class MovingReductionWindow(MovingWindow):
    def __init__(self, base, window_size=2):
        super().__init__(base, window_size=window_size)
        self.reduction_function = None
    
    def reduce_window(self, window, function=None):
        if function is None:
            function = self.reduction_function
        if function is None:
            raise NotImplementedError
        if window is None:
            return None
        else:
            return function(window)
    
    def __getitem__(self, dateindex):
        ret = super().__getitem__(dateindex)
        if isinstance(dateindex, slice):
            ret = [self.reduce_window(window) for window in ret]
        else:
            ret = self.reduce_window(ret)
        return ret
    
    def as_dateseries(self):
        data = self[:]
        return DateSeries(data=data, index=self.index)

class SMA(MovingReductionWindow):
    def __init__(self, base, window_size=2):
        super().__init__(base, window_size=window_size)
        self.reduction_function = np.mean

class Min(MovingReductionWindow):
    def __init__(self, base, window_size=2):
        super().__init__(base, window_size=window_size)
        self.reduction_function = np.min

class Max(MovingReductionWindow):
    def __init__(self, base, window_size=2):
        super().__init__(base, window_size=window_size)
        self.reduction_function = np.max
