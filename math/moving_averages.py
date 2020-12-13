import warnings
from ..types import DateSeries, DateSeriesWrapper

class EMA(DateSeriesWrapper):
    def __init__(self, base, window_size=None, alpha=None, **kwargs):
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
        
        super().__init__(base, **kwargs)
    
    def check_base(self):
        if not self.base == self.last_base:
            self.head = self.base.head
            self.last_base = self.base.copy()
            #if self.last_base.data != self.base.data:
            self.index = self.base.index.copy()
            self.data = []
            y0_init = False
            for i in range(len(self.base)):
                if self.base[i] is None:
                    self.data.append(None)
                else:
                    if not y0_init:
                        self.data.append(self.base[i])
                        y0_init = True
                    else:
                        curr_data = None
                        j = -1
                        while curr_data is None:
                            curr_data = self.data[j]
                            j -= 1
                        self.data.append(self.alpha * self.base[i] + self.inv_alpha * curr_data)
            
    
    def copy(self):
        return self.__class__(self.base, window_size=None,
                              alpha=self.alpha, data=self.data.copy(),
                              index=self.index.copy(),
                              datetime_format=self.datetime_format)

class DMA(EMA):
    def __init__(self, base, window_size=None, alpha=None, **kwargs):
        ema = EMA(base, window_size=window_size, alpha=alpha)
        super().__init__(ema, window_size=window_size, alpha=alpha,
                         **kwargs)
