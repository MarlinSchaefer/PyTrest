from ..types import DateSeries, DateSeriesWrapper
from .moving_window import SMA
from .moving_averages import EMA, DMA

class DualBaseWrapper(object):
    def __init__(self, base1, base2):
        self.base1 = base1
        self.base2 = base2
    
    def __len__(self):
        return len(self.base1)
    
    @property
    def head(self):
        try:
            return self.base1.head
        except:
            return self.base2.head
    
    @property
    def index(self):
        try:
            return self.base1.index
        except:
            return self.base2.index
    
    def check_base(self):
        pt1 = NotImplemented
        if hasattr(self.base1, 'check_base'):
            pt1 = self.base1.check_base()
        pt2 = NotImplemented
        if hasattr(self.base2, 'check_base'):
            pt2 = self.base2.check_base()
        return (pt1, pt2)
    
    def copy(self):
        return self.__class__(self.base1.copy(),
                              self.base2.copy())
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            pt1 = (self.base1 == other.base1)
            pt2 = (self.base2 == other.base2)
            return pt1 and pt2
        return False

class MACDLine(DateSeriesWrapper):
    def __init__(self, base, l_fast=None, l_slow=None, **kwargs):
        self.act_base = base
        self.l_fast = l_fast if l_fast is not None else 12
        self.l_slow = l_slow if l_slow is not None else 26
        self.ema_fast = EMA(base, window_size=self.l_fast)
        self.ema_slow = EMA(base, window_size=self.l_slow)
        self.last_base = None
        super().__init__(DualBaseWrapper(self.ema_fast,
                                         self.ema_slow), **kwargs)
    
    def check_base(self):
        super().check_base()
        if not self.base == self.last_base:
            self.head = self.base.head.copy()
            self.last_base = self.base.copy()
            ema_diff = self.ema_fast - self.ema_slow
            self.index = ema_diff.index
            self.data = ema_diff.data
    
    def copy(self):
        return self.__class__(self.act_base, l_fast=self.l_fast,
                              l_slow=self.l_slow, data=self.data.copy(),
                              index=self.index.copy(),
                              datetime_format=self.datetime_format)

class MACDSignal(EMA):
    def __init__(self, base, l_signal=9, l_fast=None, l_slow=None,
                 **kwargs):
        self.l_signal = l_signal
        if not isinstance(base, MACDLine):
            base = MACDLine(base, l_fast=l_fast, l_slow=l_slow)
        self.l_fast = base.l_fast
        self.l_slow = base.l_slow
        super().__init__(base, window_size=self.l_signal, **kwargs)
    
    @property
    def macd_line(self):
        return self.base
    
    macd = macd_line
    
    def copy(self):
        return self.__class__(self.base, l_signal=self.l_signal,
                              l_fast=self.l_fast, l_slow=self.l_slow,
                              data=self.data.copy(),
                              index=self.index.copy(),
                              datetime_format=self.datetime_format)

class Crossover(DateSeriesWrapper):
    def __init__(self, part1, part2, from_above=True, from_below=True,
                 **kwargs):
        self.part1 = part1
        self.part2 = part2
        self.from_above = from_above
        self.from_below = from_below
        super().__init__(DualBaseWrapper(self.part1,
                                         self.part2), **kwargs)
    
    def check_base(self):
        super().check_base()
        if not self.last_base == self.base:
            self.last_base = self.base.copy()
            from_above = False
            if self.from_above:
                tmp = self.part1 > self.part2
                data = []
                for i in range(len(tmp)):
                    if i == 0:
                        data.append(False)
                    else:
                        data.append(tmp[i-1] and not tmp[i])
                from_above = DateSeries(data=data, index=tmp.index,
                                        datetime_format=tmp.datetime_format)
            from_below = False
            if self.from_below:
                tmp = self.part1 < self.part2
                data = []
                for i in range(len(tmp)):
                    if i == 0:
                        data.append(False)
                    else:
                        data.append(tmp[i-1] and not tmp[i])
                from_below = DateSeries(data=data, index=tmp.index,
                                        datetime_format=tmp.datetime_format)
            combined = from_above or from_below
            if not isinstance(combined, DateSeries):
                return DateSeries(data=[False for _ in range(len(tmp))],
                                  index=tmp.index,
                                  datetime_format=tmp.datetime_format)
            self.index = combined.index
            self.data = combined.data
    
    def copy(self):
        return self.__class__(self.part1, self.part2,
                              from_above=self.from_above,
                              from_below=self.from_below,
                              data=self.data.copy(),
                              index=self.index.copy(),
                              datetime_format=self.datetime_format)
