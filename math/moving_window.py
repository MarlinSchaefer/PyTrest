import numpy as np
import warnings
import datetime
from ..types import DateSeries

class MovingWindowOperation(DateSeries):
    def __init__(self, base, min_size=None, max_size=None, **kwargs):
        self.base = base
        self.min_size = min_size
        self.max_size = max_size
        self.window_operation = kwargs.pop('window_operation', NotImplemented)
        super().__init__(**kwargs)
        self.head = self.base.head.copy()
        self.last_base = None
        self.set_window_operation()
        self.check_base()
    
    def set_window_operation(self):
        """This function is called on each window. The outputs are
        stored in this object.
        
        It must set the variable `self.window_operation` to a callable.
        
        Arguments
        ---------
        None
        
        Returns
        -------
        None
        """
        raise NotImplementedError
    
    def check_base(self):
        if not self.last_base == self.base:
            self.last_base = self.base.copy()
            self.index = self.base.index.copy()
            self.data = []
            for i in range(len(self.base)):
                if self.min_size is not None and i + 1 < self.min_size:
                    self.data.append(None)
                else:
                    stop = i + 1
                    start = 0 if self.max_size is None else max(0, stop - self.max_size)
                    window = self.base[start:stop].as_list()
                    self.data.append(self.window_operation(window))
    
    def __getitem__(self, dateindex):
        self.check_base()
        return super().__getitem__(dateindex)
    
    def copy(self):
        return self.__class__(self.base, min_size=self.min_size,
                              max_size=self.max_size,
                              window_operation=self.window_operation,
                              data=self.data.copy(),
                              index=self.index.copy(),
                              datetime_format=self.datetime_format)

class SimpleMovingWindow(MovingWindowOperation):
    def __init__(self, base, window_size=2, **kwargs):
        super().__init__(base, min_size=window_size,
                         max_size=window_size, **kwargs)
    
    def copy(self):
        return self.__class__(self.base, window_size=self.min_size,
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
