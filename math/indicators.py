from ..types.dateseries import DateSeries
from .moving_window import SMA
from .moving_averages import EMA, DMA
from ..types.events import EventMultiHandler, EventManager

class DualBaseWrapper(object):
    manager = EventManager()
    def __init__(self, base1, base2):
        self.base1 = base1
        self.base2 = base2
        handlers = [self.base1.handler, self.base2.handler]
        self.handler = EventMultiHandler(handlers=handlers)
        self.handler.listen('set_head', self.set_head_action)
    
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
        
    def set_head_action(self, event):
        dateindex = event.args[1]
        if event.emitter in [self.base1, self.base2]:
            self.set_head(dateindex)
    
    @manager.send('set_head')
    def set_head(self, dateindex):
        if self.base1.dateindex != dateindex:
            self.base1.set_head(dateindex)
        if self.base2.dateindex != dateindex:
            self.base2.set_head(dateindex)
    
    def is_parent(self, dateseries):
        own_parent = (dateseries is self.base1) or (dateseries is self.base2)
        parent_parent = (self.base1.is_parent(dateseries)) or (self.base2.is_parent(dateseries))
        return own_parent or parent_parent
    
    def copy(self):
        return self.__class__(self.base1.copy(),
                              self.base2.copy())
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            pt1 = (self.base1 == other.base1)
            pt2 = (self.base2 == other.base2)
            return pt1 and pt2
        return False

class MACDLine(DateSeries):
    def __init__(self, parent, l_fast=None, l_slow=None, **kwargs):
        super().__init__(parent)
        self.l_fast = l_fast if l_fast is not None else 12
        self.l_slow = l_slow if l_slow is not None else 26
        self.ema_fast = EMA(parent, window_size=self.l_fast)
        self.ema_slow = EMA(parent, window_size=self.l_slow)
        self.handler.listen('insert_value', self.insert_value_action)
        self.handler.listen('__setitem__', self.setitem_action)
        self.recalulate()
    
    def recalulate(self):
        ema_diff = self.ema_fast - self.ema_slow
        for dateindex, val in zip(ema_diff.index, ema_diff.data):
            if dateindex in self:
                self[dateindex] = val
            else:
                self.insert_value(dateindex, value=val)
    
    def setitem_action(self, event):
        if not (event.emitter is self.ema_fast or event.emitter is self.ema_slow):
            return
        self.recalulate()
    
    def insert_value_action(self, event):
        if not (event.emitter is self.ema_fast or event.emitter is self.ema_slow):
            return
        self.recalulate()
    
    def copy(self):
        return self.__class__(self.parent, l_fast=self.l_fast,
                              l_slow=self.l_slow, data=self.data.copy(),
                              index=self.index.copy(),
                              datetime_format=self.datetime_format)

class MACDSignal(EMA):
    def __init__(self, parent, l_signal=9, l_fast=None, l_slow=None,
                 **kwargs):
        self.l_signal = l_signal
        if not isinstance(parent, MACDLine):
            parent = MACDLine(parent, l_fast=l_fast, l_slow=l_slow)
        self.l_fast = parent.l_fast
        self.l_slow = parent.l_slow
        super().__init__(parent, window_size=self.l_signal, **kwargs)
    
    @property
    def macd_line(self):
        return self.parent
    
    macd = macd_line
    
    def copy(self):
        return self.__class__(self.parent, l_signal=self.l_signal,
                              l_fast=self.l_fast, l_slow=self.l_slow,
                              data=self.data.copy(),
                              index=self.index.copy(),
                              datetime_format=self.datetime_format)

class Crossover(DateSeries):
    def __init__(self, part1, part2, from_above=True, from_below=True,
                 **kwargs):
        self.part1 = part1
        self.part2 = part2
        self.from_above = from_above
        self.from_below = from_below
        parent = DualBaseWrapper(self.part1, self.part2)
        super().__init__(parent=parent, **kwargs)
        self.handler.listen('__setitem__', self.setitem_action)
        self.recalculate()
    
    #def set_head_action(self, event):
        #print("!!!Custom set head in dual base")
        #if event.emitter is self:
            #return
        #if not self.is_parent(event.emitter):
            #return
        #dateindex = event.args[1]
        #self.set_head(dateindex)
    
    def recalculate(self):
        from_above = False
        if self.from_above:
            tmp = self.part1 > self.part2
            data = []
            for i in range(len(tmp)):
                if i == 0:
                    data.append(False)
                else:
                    data.append(tmp.iloc(i-1) and not tmp.iloc(i))
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
            tmp = self.parent
            combined = DateSeries(data=[False for _ in range(len(tmp))],
                                  index=tmp.index,
                                  datetime_format=tmp.datetime_format)
        
        for dateindex, data_pt in zip(combined.index, combined.data):
            if dateindex not in self:
                self.insert_value(dateindex, value=data_pt)
            else:
                self[dateindex] = data_pt
    
    def setitem_action(self, event):
        if self.parent.is_parent(event.emitter):
            self.recalculate()
    
    #def set_head_action(self, event):
        #if self.parent.is_parent(event.emitter):
            #self.recalculate()
    
    def copy(self):
        return self.__class__(self.part1, self.part2,
                              from_above=self.from_above,
                              from_below=self.from_below,
                              data=self.data.copy(),
                              index=self.index.copy(),
                              datetime_format=self.datetime_format)
