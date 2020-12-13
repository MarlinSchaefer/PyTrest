import datetime
import numpy as np
import matplotlib.pyplot as plt

class DateSeries(object):
    def __init__(self, data=None, index=None,
                 datetime_format='%d.%m.%Y %H:%M:%S'):
        #head = Read-head [index position, datetime]
        if data is None:
            self.data = []
        else:
            self.data = data
        if index is None:
            self.index = []
        else:
            self.index = index
        assert len(self.data) == len(self.index)
        if len(self.index) == 0:
            self.head = [-1, None]
        else:
            self.head = [0, self.index[0]]
        self.datetime_format = datetime_format
    
    def __contains__(self, item):
        if isinstance(item, datetime.datetime):
            return item in self.index
        else:
            return item in self.data
    
    def __len__(self):
        return len(self.data)
    
    @property
    def value(self):
        return self.data[self.head[0]]
    
    @property
    def head_date(self):
        return self.head[1]
    
    @property
    def dateindex(self):
        return self.head_date
    
    @property
    def head_index(self):
        return self.head[0]
    
    @property
    def min_dateindex(self):
        try:
            return min(self.index)
        except:
            return None
    
    @property
    def max_dateindex(self):
        try:
            return max(self.index)
        except:
            return None
    
    def insert_value(self, dateindex, value=None):
        if len(self.index) == 0:
            self.index.append(dateindex)
            self.data.append(value)
            
            self.head = [0, self.index[0]]
        else:
            idx = np.searchsorted(np.array(self.index), dateindex)
            if idx < len(self.index):
                if self.index[idx] == dateindex:
                    msg = 'Cannot insert when index is already occupied. '
                    raise IndexError(msg)
        
            #Check if head needs to be moved
            if idx < self.head[0]:
                self.head[0] += 1
            
            self.index.insert(idx, dateindex)
            self.data.insert(idx, value)
        
    
    def set_head(self, dateindex):
        idx = np.searchsorted(np.array(self.index), dateindex)
        if not self.index[idx] == dateindex:
            return False
        self.head = [idx, dateindex]
        return True
    
    def set_head_closest(self, dateindex):
        idx = np.searchsorted(np.array(self.index), dateindex)
        idx += np.argmin(np.abs([self.index[idx]-dateindex,
                                 self.index[idx+1]-dateindex]))
        self.head = [idx, self.index[idx]]
    
    def set_head_or_prior(self, dateindex):
        if dateindex in self.index:
            self.set_head(dateindex)
        else:
            idx = np.searchsorted(np.array(self.index), dateindex)
            self.head = [idx-1, self.index[idx-1]]
    
    def __next__(self):
        if self.head[0] >= len(self) - 1:
            raise StopIteration()
        self.head[0] += 1
        self.head[1] = self.index[self.head[0]]
        return self.value
    
    def next_date(self):
        if self.head[0] >= len(self) - 1:
            return self.head[1]
        else:
            return self.index[self.head[0] + 1]
    
    def advance_head(self, timeindex, use_closest=False):
        posmsg = 'Can advance the read-head only in the positive '
        posmsg += 'direction.'
        
        idxmsg = 'Index is out of range of the available data. Use the '
        idxmsg += 'option `use_closest` to set the head to the last '
        idxmsg += 'available position.'
        if isinstance(timeindex, int):
            if timeindex < 0:
                raise ValueError(posmsg)
            if self.head[0] + timeindex >= len(self) - 1:
                if use_closest:
                    timeindex = len(self) - self.head[0]
                else:
                    raise IndexError(idxmsg)
            self.head[0] += timeindex
            self.head[1] = self.index[self.head[0]]
            return True
        elif isinstance(timeindex, datetime.timedelta):
            if timeindex < datetime.timedelta(seconds=0):
                raise ValueError(posmsg)
            if self.head[1] + timedelta > self.index[-1]:
                if use_closest:
                    timedelta = self.index[-1] - self.head[1]
                else:
                    raise IndexError(idxmsg)
            if use_closest:
                self.set_head_closest(self.head[1] + timeindex)
                return True
            else:
                return self.set_head(self.head[1] + timedelta)
    
    def iloc(self, index):
        if index < 0:
            index = len(self) + index
        if index < 0 or index >= len(self):
            raise IndexError('Index out of range.')
        return self.data[index]
    
    def rloc(self, index):
        """Return the value relative to the read-head.
        
        This function reduces the allowed index-range to [0, read-head].
        For positive integers within this range the call to this
        function is equivalent to a call to iloc. For negative integers
        not the last entry of the DateSeries is taken as reference, but
        the position of the read-head.
        
        Arguments
        ---------
        index : int
            The index relative to the read-head from which data should
            be retrieved.
        
        Returns
        -------
        object:
            The object stored at the index location.
        """
        if index < 0:
            index = self.head[0] + 1 + index
        if index < 0 or index > self.head[0]:
            raise IndexError('Index out of range.')
        return self.data[index]
    
    def loc(self, dateindex, use_closest=False):
        original_head = self.head.copy()
        if use_closest:
            self.set_head_closest(dateindex)
        else:
            success = self.set_head(dateindex)
            if not success:
                msg = 'Datetime {} is not contained in the index.'
                msg = msg.format(dateindex)
                raise IndexError(msg)
        ret = self.value
        self.head = original_head
        return ret
    
    def sanitize_slice(self, dateindex):
        if isinstance(dateindex, slice):
            #Clean up start, stop and step
            start = dateindex.start
            stop = dateindex.stop
            step = dateindex.step
            
            #Handle start is None
            if start is None:
                if stop is None:
                    if step is None:
                        start = 0
                        stop = len(self)
                        step = 1
                    elif isinstance(step, int):
                        start = 0
                        stop = len(self)
                    elif isinstance(step, datetime.timedelta):
                        start = self.index[0]
                        stop = self.index[-1]
                    else:
                        msg = 'Unrecognized type for step.'
                        raise TypeError(msg)
                elif isinstance(stop, int):
                    start = 0
                elif isinstance(stop, (datetime.datetime, str)):
                    start = self.index[0]
                else:
                    msg = 'Unrecognized type for stop.'
                    raise TypeError(msg)
            
            #Handle start is integer
            if isinstance(start, int):
                if isinstance(stop, (datetime.datetime, str)):
                    start = self.index[start]
                elif stop is None:
                    #This is the only case where we loop over integers
                    stop = len(self)
                    if step is None:
                        step = 1
                elif not isinstance(stop, int):
                    msg = 'When accessing a slice and the start index '
                    msg += 'is an integer, the stop index must be '
                    msg += 'either another integer, a datetime or a '
                    msg += 'string specifying a datetime.'
                    raise TypeError(msg)
            
            #Handle string start, stop, step
            if isinstance(start, str):
                start = datetime.datetime.strptime(start, self.datetime_format)
            if isinstance(stop, str):
                stop = datetime.datetime.strptime(stop, self.datetime_format)
            if isinstance(step, str):
                msg = 'The step of the given slice must not be a string.'
                msg += ' It has to be either None, an integer or a '
                msg += 'datetime.timedelta.'
                raise TypeError(msg)
            
            #Handle any datetime-slices
            if isinstance(start, datetime.datetime):
                if stop is None:
                    stop = self.index[-1]
                elif isinstance(stop, int):
                    stop = self.index[stop]
                elif not isinstance(stop, datetime.datetime):
                    msg = 'Unrecognized type for stop.'
                    raise TypeError(msg)
                if not isinstance(step, datetime.timedelta):
                    msg = 'When using datetime to slice data a step in '
                    msg += 'form of a datetime.timedelta must be '
                    msg += 'provided.'
                    raise TypeError(msg)
            return start, stop, step
        else:
            msg = 'sanitize_slice expected a slice as input type. Got '
            msg += '{} instead.'
            msg = msg.format(type(dateindex))
            raise TypeError(msg)
    
    def __getitem__(self, dateindex):
        if isinstance(dateindex, slice):
            start, stop, step = self.sanitize_slice(dateindex)
            
            #Loop over the slice
            ret = []
            ind = []
            if isinstance(start, int):
                if step is None:
                    step = 1
                for i in range(start, stop, step):
                    ret.append(self.iloc(i))
                    ind.append(self.index[i])
            elif isinstance(start, datetime.datetime):
                curr = min(start, stop)
                step = abs(step)
                while curr < max(start, stop):
                    ret.append(self.loc(curr))
                    ind.append(curr)
                    curr += step
            else:
                msg = 'Uncaught type-error with (start, stop, step) = '
                msg += '({}, {}, {}).'.format(start, stop, step)
                raise RuntimeError(msg)
                pass
            return DateSeries(data=ret, index=ind,
                              datetime_format=self.datetime_format)
        elif isinstance(dateindex, int):
            return self.iloc(dateindex)
        elif isinstance(dateindex, str):
            dateindex = datetime.datetime.strptime(dateindex, self.datetime_format)
        if isinstance(dateindex, datetime.datetime):
            return self.loc(dateindex)
        raise TypeError('Unrecognized type.')
    
    def as_list(self):
        return self.data
    
    def copy(self):
        ret = self.__class__(data=self.data.copy(),
                             index=self.index.copy(),
                             datetime_format=self.datetime_format)
        ret.head = self.head.copy()
        return ret
    
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
        x_float = []
        y_float = []
        for x, y in zip(self.index, self.data):
            try:
                y_float.append(float(y))
                x_float.append(x)
            except:
                pass
        if len(y_float) < 2:
            return fig, ax
        ax.plot(x_float, y_float, **kwargs)
        return fig, ax
    
    #All math functionality
    def binary_operation(self, other, function_name):
        if isinstance(other, DateSeries):
            #print("Other is DateSeries, Trying to call function {}".format(function_name))
            index = []
            data = []
            for dateindex in self.index:
                if dateindex in other.index:
                    index.append(dateindex)
                    func = getattr(self.loc(dateindex), function_name)
                    data.append(func(other.loc(dateindex)))
            ret = DateSeries(data=data, index=index)
            ret.head = [0, index[0]]
            return ret
        else:
            try:
                length = len(other)
            except:
                #Expecting a scalar value here
                data = []
                for dat in self.data:
                    func = getattr(dat, function_name)
                    data.append(func(other))
                ret = DateSeries(data=data, index=self.index)
                ret.head = self.head
                return ret
            else:
                if length == len(self):
                    data = []
                    for i, dat in enumerate(self, data):
                        func = getattr(dat, function_name)
                        data.append(func(other[i]))
                    ret = DateSeries(data=data, index=self.index)
                    ret.head = self.head
                    return ret
                else:
                    raise ValueError('Lengths do not match.')
    
    def __add__(self, other):
        return self.binary_operation(other, '__add__')
    
    def __radd__(self, other):
        return self.binary_operation(other, '__radd__')
    
    def __sub__(self, other):
        return self.binary_operation(other, '__sub__')
    
    def __rsub__(self, other):
        return self.binary_operation(other, '__rsub__')
    
    def __mul__(self, other):
        return self.binary_operation(other, '__mul__')
    
    def __rmul__(self, other):
        return self.binary_operation(other, '__rmul__')
    
    def __truediv__(self, other):
        return self.binary_operation(other, '__truediv__')
    
    def __rtruediv__(self, other):
        return self.binary_operation(other, '__rtruediv__')
    
    def __lt__(self, other):
        return self.binary_operation(other, '__lt__')
    
    def __le__(self, other):
        return self.binary_operation(other, '__le__')
    
    def __gt__(self, other):
        return self.binary_operation(other, '__gt__')
    
    def __ge__(self, other):
        return self.binary_operation(other, '__ge__')
    
    def __neg__(self):
        data = [-dat for dat in self.data]
        index = self.index
        datetime_format = self.datetime_format
        return DateSeries(data=data, index=index,
                          datetime_format=datetime_format)
    
    def __eq__(self, other):
        if isinstance(other, type(self)):
            data = (self.data == other.data)
            index = (self.index == other.index)
            return (data and index)
        else:
            return False
    
    def __array__(self):
        prep_index = [np.datetime64(date) for date in self.index]
        prep_values = []
        for val in self.data:
            try:
                prep_values.append(float(val))
            except:
                prep_values.append(val)
        content = [(np.datetime64(date), val) for (date, val) in zip(prep_index, prep_values)]
        return np.array(content, dtype=[('dateindex', np.dtype('datetime64[us]')),
                                        ('data', np.array(prep_values).dtype)])
    
    def __array__ufunc__(self, ufunc, method, *inputs, **kwargs):
        func = getattr(ufunc, method)
        act_inputs = []
        for inp in inputs:
            if isinstance(inp, self.__class__):
                act_inputs.append(inp.data)
            else:
                return NotImplemented
        return func(*act_inputs, **kwargs)

class DateSeriesWrapper(DateSeries):
    def __init__(self, base, **kwargs):
        self.base = base
        self.last_base = None
        super().__init__(**kwargs)
        self.head = self.base.head.copy()
        if self.check_base() is NotImplemented:
            msg = 'Trying to use the base-class `DateSeriesWrapper`. '
            msg += 'Please inherit from this class and implement the '
            msg += 'function `check_base`. See details on the '
            msg += 'implementation in the docstring of the function.'
            raise NotImplementedError(msg)
    
    def __getitem__(self, dateindex):
        if self.check_base() is NotImplemented:
            msg = 'Trying to use the base-class `DateSeriesWrapper`. '
            msg += 'Please inherit from this class and implement the '
            msg += 'function `check_base`. See details on the '
            msg += 'implementation in the docstring of the function.'
            raise NotImplementedError(msg)
        return super().__getitem__(dateindex)
    
    def check_base(self):
        """This function checks the base-DateSeries for any changes. If
        changes are detected the content of this DateSeries is updated.
        
        Please implement it by using the following skeleton:
        
        def check_base(self):
            super().check_base()
            if not self.base == self.last_base:
                #Code to calculate the contents of this wrapper
        """
        if hasattr(self.base, 'check_base'):
            self.base.check_base()
        return NotImplemented
    
    def copy(self):
        return self.__class__(self.base, data=self.data,
                              index=self.index,
                              datetime_format=self.datetime_format)
