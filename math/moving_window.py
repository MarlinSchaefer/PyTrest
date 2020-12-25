import numpy as np
import warnings
import datetime
from ..types.dateseries_synced import DateSeries

class MovingWindowOperation(DateSeries):
    def __init__(self, parent, min_size=None, max_size=None, **kwargs):
        self.window_operation = kwargs.pop('window_operation', NotImplemented)
        self.min_size = min_size
        self.max_size = max_size
        self.set_window_operation()
        super().__init__(parent, **kwargs)
        self.handler.listen('insert_value', self.insert_value_action)
        self.handler.listen('__setitem__', self.setitem_action)
        self.calculate_windows_from_index(0)
    
    def calculate_windows_from_index(self, index):
        if index >= len(self):
            if index >= len(self.parent):
                return
            for i in range(len(self), index+1):
                self.insert_value(self.parent.index[i], value=None)
            
        for i in range(index, len(self.parent)):
            curr_dateindex = self.parent.index[i]
            if self.min_size is not None and i + 1 < self.min_size:
                if curr_dateindex in self:
                    self[curr_dateindex] = None
                else:
                    self.insert_value(curr_dateindex, value=None)
            else:
                stop = i + 1
                start = 0 if self.max_size is None else max(0, stop - self.max_size)
                window = self.parent[start:stop].as_list()
                val = self.window_operation(window)
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
            self.calculate_windows_from_index(dateindex)
        else:
            raise TypeError
    
    def insert_value_action(self, event):
        if event.emitter is self:
            return
        if not self.is_parent(event.emitter):
            return
        dateindex = event.args[1]
        i = self.parent.index.index(dateindex)
        self.calculate_windows_from_index(i)
    
    def copy(self):
        return self.__class__(self.parent, min_size=self.min_size,
                              max_size=self.max_size,
                              window_operation=self.window_operation,
                              data=self.data.copy(),
                              index=self.index.copy(),
                              datetime_format=self.datetime_format)

class SimpleMovingWindow(MovingWindowOperation):
    def __init__(self, parent, window_size=2, **kwargs):
        super().__init__(parent, min_size=window_size,
                         max_size=window_size, **kwargs)
    
    def copy(self):
        return self.__class__(self.parent, window_size=self.min_size,
                              window_operation=self.window_operation,
                              data=self.data.copy(),
                              index=self.index.copy(),
                              datetime_format=self.datetime_format)

class MovingWindow(SimpleMovingWindow):
    def set_window_operation(self):
        self.window_operation = lambda inp: inp

class SMA(SimpleMovingWindow):
    def set_window_operation(self):
        self.window_operation = lambda window: None if None in window else np.mean(window)

class Min(SimpleMovingWindow):
    def set_window_operation(self):
        self.window_operation = lambda window: None if None in window else np.min(window)

class Max(SimpleMovingWindow):
    def set_window_operation(self):
        self.window_operation = lambda window: None if None in window else np.max(window)

class Std(SimpleMovingWindow):
    def set_window_operation(self):
        self.window_operation = lambda window: None if None in window else np.std(window)

#class MovingTransformationWindow(DateSeries):
    #def __init__(self, base, window_size=2):
        #self.base = base
        #self.window_size = window_size
        #super().__init__()
        #self.head = self.base.head.copy()
        #self.last_base = None
        #self.set_transformation()
        #self.check_base()
    
    #def set_transformation(self):
        #"""This function transforms the contents of a window. Only the
        #transformed data is stored.
        
        #It must set the variable `self.transform` to a callable.
        
        #Arguments
        #---------
        #None
        
        #Returns
        #-------
        #None
        #"""
        #raise NotImplementedError
    
    #def check_base(self):
        #if not self.last_base == self.base:
            #self.last_base = self.base.copy()
            #self.index = self.base.index.copy()
            #self.data = []
            #for i in range(len(self.base)):
                #if i < self.window_size - 1:
                    #self.data.append(None)
                #else:
                    #window = self.base[i-self.window_size+1:i+1]
                    #self.data.append(self.transform(window))
            #self.index = self.base.index.copy()
    
    #def __getitem__(self, dateindex):
        #self.check_base()
        #return super().__getitem__(dateindex)

#class MovingWindow(MovingTransformationWindow):
    #def set_transformation(self):
        #self.transform = lambda inp: inp

#class SMA(MovingTransformationWindow):
    #def set_transformation(self):
        #self.transform = np.mean

#class Min(MovingTransformationWindow):
    #def set_transformation(self):
        #self.transform = np.min

#class Max(MovingTransformationWindow):
    #def set_transformation(self):
        #self.transform = np.max
