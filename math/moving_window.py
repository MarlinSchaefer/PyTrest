import numpy as np
import warnings
import datetime
from ..types import DateSeries

class MovingTransformationWindow(DateSeries):
    def __init__(self, base, window_size=2):
        self.base = base
        self.window_size = window_size
        super().__init__()
        self.head = self.base.head.copy()
        self.last_base = None
        self.set_transformation()
        self.check_base()
    
    def set_transformation(self):
        """This function transforms the contents of a window. Only the
        transformed data is stored.
        
        It must set the variable `self.transform` to a callable.
        
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
                if i < self.window_size - 1:
                    self.data.append(None)
                else:
                    window = self.base[i-self.window_size+1:i+1]
                    self.data.append(self.transform(window))
            self.index = self.base.index.copy()
    
    def __getitem__(self, dateindex):
        self.check_base()
        return super().__getitem__(dateindex)

class MovingWindow(MovingTransformationWindow):
    def set_transformation(self):
        self.transform = lambda inp: inp

class SMA(MovingTransformationWindow):
    def set_transformation(self):
        self.transform = np.mean

class Min(MovingTransformationWindow):
    def set_transformation(self):
        self.transform = np.min

class Max(MovingTransformationWindow):
    def set_transformation(self):
        self.transform = np.max
