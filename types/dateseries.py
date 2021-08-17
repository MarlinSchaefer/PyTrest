"""This module contains the core type of this library; the DateSeries.
It is a class that stores arbitrary data ordered by a datetime index and
exposes easy access functions.
"""
import datetime
import numpy as np
import matplotlib.pyplot as plt
from .events import EventManager, EventHandler

class DateSeries(object):
    """Core object for handling data sorted by datetime indices.
    
    This object stores arbitrary data indexed by datetimes. It can be
    manipulated by external events. It allows for easy access and tracks
    the position of a current read head.
    
    Arguments
    ---------
    parent : {None or DateSeries like object, None}
        A DateSeries from which this instance is derived. Certain action
        may be synchronised with this parent.
    data : {list or None, None}
        A list of initial data. If None, an empty list is initialized.
        Must be of same length as index.
    index : {list or None, None}
        A list of datetimes corresponding to the elements in data. If
        None an empty list is initialized. Must be of same length as
        data.
    datetime_format : {str, '%d.%m.%Y %H:%M:%S'}
        A string which is used to encode datetimes as strings and decode
        strings into datetime objects.
    
    Properties
    ----------
    value:
        The element of the contained data at the current read head
        postion.
    dateindex/head_date:
        The datetime in the index at the current read head postion.
    head_index:
        The integer index of the current read head position.
    min_dateindex:
        The minimum dateindex contained in the index.
    max_dateindex:
        The maximum dateindex contained in the index.
    """
    manager = EventManager()
    def __init__(self, parent=None, data=None, index=None,
                 datetime_format='%d.%m.%Y %H:%M:%S'):
        self.parent = parent
        if self.parent is None:
            self.handler = EventHandler()
        else:
            self.handler = parent.handler
        
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
        self.handler.listen('set_head', self.set_head_action)
    
    def __contains__(self, item):
        if isinstance(item, datetime.datetime):
            return item in self.index
        else:
            return item in self.data
    
    def __len__(self):
        return len(self.data)
    
    def is_parent(self, dateseries):
        """Check if a DateSeries is known as the parent to this
        instance.
        
        Arguments
        ---------
        dateseries : object
            An object of which to check if it is the parent of this
            instance.
        
        Returns
        -------
        bool:
            True if the object is the parent of this instance, False
            otherwise.
        """
        return dateseries is self.parent
    
    @property
    def value(self):
        """The element in the stored data at the current read head
        position.
        """
        return self.data[self.head[0]]
    
    @property
    def head_date(self):
        """The dateindex stored in the index at the current read head
        position.
        """
        return self.head[1]
    
    @property
    def dateindex(self):
        """Synonym to self.head_date. The dateindex stored in the index
        at the current read head position.
        """
        return self.head_date
    
    @property
    def head_index(self):
        """The integer index of the current read head position.
        """
        return self.head[0]
    
    @property
    def min_dateindex(self):
        """The minimum datetime contained in the index.
        """
        try:
            return min(self.index)
        except:
            return None
    
    @property
    def max_dateindex(self):
        """The maximum datetime contained in the index.
        """
        try:
            return max(self.index)
        except:
            return None
    
    @manager.send('insert_value')
    def insert_value(self, dateindex, value=None):
        """Insert a value into the DateSeries.
        
        This method sends an event for synchronisation when called.
        
        Arguments
        ---------
        dateindex : datetime
            The datetime at which to insert a value.
        value : {object, None}
            The object to insert into the DateSeries.
        """
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
        
    @manager.send('set_head')
    def set_head(self, dateindex):
        """Set the read head to a given dateindex.
        
        Sends an event for synchronisation purposes when called. Use
        `self.set_head_silent` to avoid sending an event. (Recommended
        only when the head is adjusted temporarily.)
        
        Arguments
        ---------
        dateindex : datetime
            The datetime which to set the head to. Must be contained in
            the index to set the head successfully.
        
        Returns
        -------
        bool:
            Returns True if the head was set successfully, False
            otherwise.
        """
        idx = np.searchsorted(np.array(self.index), dateindex)
        if not self.index[idx] == dateindex:
            return False
        self.head = [idx, dateindex]
        return True
    
    def set_head_silent(self, dateindex):
        """Same as `self.set_head` but without sending an event for
        synchronisation purposes.
        
        Use with care.
        
        Arguments
        ---------
        dateindex : datetime
            The datetime which to set the head to. Must be contained in
            the index to set the head successfully.
        
        Returns
        -------
        bool:
            Returns True if the head was set successfully, False
            otherwise.
        """
        idx = np.searchsorted(np.array(self.index), dateindex)
        if not self.index[idx] == dateindex:
            return False
        self.head = [idx, dateindex]
        return True
    
    def set_head_action(self, event):
        """The function that is called when a `set_head` action is
        received. If the emitter of the event is a parent of this
        instance the head is adjusted to the same position.
        
        Arguments
        ---------
        event : Event
            A PyTrest.types.events.Event.
        
        """
        if event.emitter is self:
            return
        if not self.is_parent(event.emitter):
            return
        dateindex = event.args[1]
        self.set_head(dateindex)
    
    def set_head_closest(self, dateindex):
        """Set the read head to the dateindex of the index closest to
        the provided dateindex.
        
        This function sends a `set_head` event for synchronisation
        purposes. Use `self.set_head_closest_silent` to avoid sending
        such an event.
        
        Arguments
        ---------
        dateindex : datetime
            The datetime to use as reference to find the closest
            dateindex within this DateSeries. Sets the read head to the
            closest found dateindex.
        """
        idx = np.searchsorted(np.array(self.index), dateindex)
        idx += np.argmin(np.abs([self.index[idx]-dateindex,
                                 self.index[idx+1]-dateindex]))
        self.set_head(self.index[idx])
    
    def set_head_closest_silent(self, dateindex):
        """Same as `self.set_head_closest` without sending an event.
        
        Arguments
        ---------
        dateindex : datetime
            The datetime to use as reference to find the closest
            dateindex within this DateSeries. Sets the read head to the
            closest found dateindex.
        """
        idx = np.searchsorted(np.array(self.index), dateindex)
        idx += np.argmin(np.abs([self.index[idx]-dateindex,
                                 self.index[idx+1]-dateindex]))
        self.set_head_silent(self.index[idx])
    
    def set_head_or_prior(self, dateindex):
        """Set the read head to the given dateindex or the closest
        available datetime before the provided location.
        
        Arguments
        ---------
        dateindex : datetime
            The maximum datetime to set the read head to. Set the read
            head to this datetime or the closest prior datetime.
        """
        if dateindex in self.index:
            self.set_head(dateindex)
        else:
            idx = np.searchsorted(np.array(self.index), dateindex)
            self.set_head(self.index[idx-1])
    
    def __next__(self):
        """Return the next value in the DateSeries from the read head.
        Advances the read head by one index.
        """
        if self.head[0] >= len(self) - 1:
            raise StopIteration()
        self.set_head(self.index[self.head[0]+1])
        return self.value
    
    def next_date(self):
        """Return the datetime following the current read head position.
        If the read head is at the end return the current datetime.
        """
        if self.head[0] >= len(self) - 1:
            return self.head[1]
        else:
            return self.index[self.head[0] + 1]
    
    def advance_head(self, timeindex, use_closest=False):
        """Advance the read head by a given number of steps or a given
        time delta.
        
        Arguments
        ---------
        timeindex : int >= 0 or timedelta
            The amount of time (timedelta) or the number of dateindices
            (int) to advance the read head by. If an integer value is
            used it has to be positive.
        use_closest : {bool, False}
            Whether or not to use the closest available dateindex when
            the timeindex does not hit an allowed position. (Either by
            hitting the end of available data or by landing between
            dateindices in the index.)
        
        Raises
        ------
        ValueError:
            Raises a ValueError if the provided timeindex is negative.
        IndexError:
            Raises an IndexError if no fitting index can be found.
        """
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
            self.set_head(self.index[self.head[0]+timeindex])
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
        """The value at a given index-location. This index has to be an
        integer and allows to access the values of the DateSeries like a
        normal list.
        
        Arguments
        ---------
        index : int
            The index at which to access the data.
        """
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
        """Return the value of data at a given datetime.
        
        Arguments
        ---------
        dateindex : datetime
            The datetime at which to access the data.
        use_closest : {Bool, False}
            Whether or not to use the closest datetime, if the provided
            dateindex is not contained in the index.
        
        Returns
        -------
        object:
            The value stored in data at the given location.
        """
        original_head = self.head.copy()
        if use_closest:
            self.set_head_closest_silent(dateindex)
        else:
            success = self.set_head_silent(dateindex)
            if not success:
                msg = 'Datetime {} is not contained in the index.'
                msg = msg.format(dateindex)
                raise IndexError(msg)
        ret = self.value
        self.head = original_head
        return ret
    
    def sanitize_slice(self, dateindex):
        """Sanitice the user input when accessing the DateSeries using a
        slice.
        
        Arguments
        ---------
        dateindex : slice
            A slice that should be used to access the data. The slice
            may contain integers, datetimes (where the step has to be a
            timedelta) or strings representing datetimes.
        
        Returns
        -------
        start : int or datetime
            The starting index of the slice.
        stop : int or datetime
            The stopping index of the slice.
        step : int or timedelta or None
            The step for the slice.
        """
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
        """Access the data in the DateSeries through the usual list
        syntax: DateSeries[index].
        
        dateindex : int or str or datetime or slice of the previous or None
            The dateindex at which to access the data. If a string is
            provided it has to be decodable into a datetime using the
            DateSeries.datetime_format.
        """
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
    
    @manager.send('__setitem__')
    def __setitem__(self, dateindex, value):
        """Set the value of elements in the data using the usual list
        syntax: DateSeries[index] = value.
        
        Sends a `__setitem__` event for synchronisation purposes when
        called.
        
        Arguments
        ---------
        dateindex : index accepted by __getitem__
            The dateindex at which to set the data. May be a slice.
        value : object
            The object to set the value of all accessed indices to.
            Care, if an iterable is provided, the data values are not
            set to the values of the iterable but all values are set to
            the entire iterable.
        """
        if isinstance(dateindex, slice):
            start, stop, step = self.sanitize_slice(dateindex)
            
            #Loop over the slice
            ret = []
            ind = []
            if isinstance(start, int):
                if step is None:
                    step = 1
                for i in range(start, stop, step):
                    self.data[i] = value
            elif isinstance(start, datetime.datetime):
                curr = min(start, stop)
                step = abs(step)
                while curr < max(start, stop):
                    if curr in self.index:
                        i = self.index.index(curr)
                    else:
                        continue
                    self.data[i] = value
                    curr += step
            else:
                msg = 'Uncaught type-error with (start, stop, step) = '
                msg += '({}, {}, {}).'.format(start, stop, step)
                raise RuntimeError(msg)
                pass
            self.data
            return
        elif isinstance(dateindex, int):
            self.data[dateindex] = value
            return
        elif isinstance(dateindex, str):
            dateindex = datetime.datetime.strptime(dateindex, self.datetime_format)
        if isinstance(dateindex, datetime.datetime):
            if dateindex in self.index:
                i = self.index.index(dateindex)
            else:
                raise ValueError('Dateindex {} not in DateSeries.'.format(dateindex))
            self.data[i] = value
            return
        raise TypeError('Unrecognized type.')
    
    def as_list(self):
        """Return the contents of the entire DateSeries as list.
        Equivalent to calling DateSeries.data.
        
        Returns
        -------
        list of objects:
            The data stored in this DateSeries.
        """
        return self.data
    
    def copy(self):
        """Copy the contents of this DateSeries to a new instance.
        
        Returns
        -------
        DateSeries
        """
        ret = self.__class__(data=self.data.copy(),
                             index=self.index.copy(),
                             datetime_format=self.datetime_format)
        ret.head = self.head.copy()
        return ret
    
    def as_dict(self):
        """Serialize this object to a dictionary.
        
        Returns
        -------
        dict:
            A dictionary containing all information but the read head
            position of this object.
        """
        ret = {}
        ret['data'] = self.data
        ret['index'] = [pt.strftime(self.datetime_format) for pt in self.index]
        ret['datetime_format'] = self.datetime_format
        return ret
    
    @classmethod
    def from_dict(cls, dic):
        """Load a DateSeries from a dictionary output by
        DateSeries.as_dict.
        
        Arguments
        ---------
        dic : dict
            A dictionary containing keys `data`, `index`, and
            `datetime_format`.
        
        Returns
        -------
        DateSeries:
            The DateSeries loaded from the dictionary.
        """
        data = dic.get('data', [])
        index = dic.get('index', [])
        dtf = dic.get('datetime_format', '%d.%m.%Y %H:%M:%S')
        assert len(data) == len(index)
        index = [datetime.datetime.strptime(pt, dtf) for pt in index]
        return DateSeries(data=data, index=index, datetime_format=dtf)
    
    def plot(self, fig=None, ax=None, **kwargs):
        """Plot the contents of this DateSeries, if possible.
        
        Uses matplotlib to do the plotting.
        
        Arguments
        ---------
        fig : {matplotlib.pyplot.Figure or None, None}
            The figure to use for plotting purposes.
        ax : {matplotlib.pyplot.Axes or None, None}
            The axes to use for plotting purposes.
        **kwargs : 
            All other keyword arguments are passed to
            matplotlib.pyplot.Axes.plot.
        
        Returns
        -------
        fig : matplotlib.pyplot.Figure
            The figure that was used for plotting.
        ax : matplotlib.pyplot.Axes
            The axes that was used for plotting.
        
        Notes
        -----
        -If no figure or axes are provided, new instances will be
         created.
        -Only data values that contain a `__float__` conversion are
         plotted.
        """
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
