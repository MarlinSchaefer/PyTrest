import matplotlib.pyplot as plt
from ..types import DateSeries

class OptionWrapper(object):
    def __init__(self, dateseries, kwargs):
        self.dateseries = dateseries
        self.kwargs = kwargs
    
    def plot(self):
        return self.dateseries.plot(**self.kwargs)

def plot(args, show=False, store=False, default_orientation='v',
         legend=False, grid=False):
    """This function provides an easy to use interface to plot multiple
    DateSeries objects.
    
    An individual subplot can be specified by an atomic piece:
    -DateSeries => plot only this one DateSeries in the subplot with no
     options
    -(DateSeries, dict), where the dict contains options for the
     individual subplot => plot only this one DateSeries in the subplot
     but use the provided options
    -(DateSeries, DateSeries, ...) => plot all provided DateSeries in
     the same subplot but use no options for any of them
    -(DateSeries, (DateSeries, dict), ...) => plot all provided
     DateSeries in the same plot. Apply the options specified in the
     dict to the plots where they were given.
    
    To plot multiple subplots (i.e. have multiple plots on the same
    canvas) a structure can be provided by passing a list of depth one
    or two. The lists should be equivalent to a 1D or 2D array, i.e. for
    a list of depth 2 all lists on the second level should have the same
    length. The first index of the list specifies the row, the second
    index of the list should specify the column. (In a 1D-case the
    positioning is handled by the option `default_orientation`) The
    contents of the array-like list should be the atomic-pieces
    described above.
    If a panel should be left blank, the according spot in the
    array-like list must be None.
    
    Arguments
    ---------
    default_orientation : {'v' or 'h', 'v'}
        If only a list of different 
    
    Examples
    --------
    >>> plot(DateSeries(x))
    >>>
    out: Plots the contents of x.
         
         #####
         #(x)#
         #####
    
    >>> plot((DateSeries(x), options))
    >>>
    out: Plots the contents of x using the provided options.
         
         #####
         #(x)#
         #####
    
    >>> plot((DateSeries(x), DateSeries(y)))
    >>>
    out: Plots the contents of x and y in the same panel.
         
         ########
         #(x, y)#
         ########
    
    >>> plot([DateSeries(x), DateSeries(y)], default_orientation='v')
    >>>
    out: Plots the contents of x and y in different panels. The panels
         are stacked vertically.
         
         #####
         #(x)#
         #####
         #(y)#
         #####
    
    >>> plot([DateSeries(x), DateSeries(y)], default_orientation='h')
    >>>
    out: Plots the contents of x and y in different panels. The panels
         are stacked horizontally.
         
         #########
         #(x)#(y)#
         #########
    
    >>> plot([(DateSeries(x), optionsX), DateSeries(y)], \
    >>>      default_orientation='v')
    >>>
    out: Plots the contents of x and y in different panels. The panels
         are stacked vertically. The options provided in `optionsX` are
         applied to the top panel only.
         
         #####
         #(x)#
         #####
         #(y)#
         #####
    
    >>> plot([[DateSeries(x)], [DateSeries(y)]])
    >>>
    out: Plots the contents of x and y in different panels. The panels
         are stacked vertically.
         
         #####
         #(x)#
         #####
         #(y)#
         #####
    
    >>> plot([[DateSeries(x), DateSeries(y)]])
    >>>
    out: Plots the contents of x and y in different panels. The panels
         are stacked horizontally.
         
         #########
         #(x)#(y)#
         #########
    
    >>> plot([[DateSeries(w), DateSeries(x)],\
    >>>       [DateSeries(y), DateSeries(z)]])
    >>>
    out: Plots the contents of w, x, y and z in different panels. The
         panels are arranged in a 2 by 2 grid.
         
         #########
         #(w)#(x)#
         #########
         #(y)#(z)#
         #########
    
    >>> plot([[(DateSeries(w), optionsW), DateSeries(x)],\
    >>>       [DateSeries(y), (DateSeries(z), optionsZ)]])
    >>>
    out: Plots the contents of w, x, y and z in different panels. The
         panels are arranged in a 2 by 2 grid. The options specified in
         `optionsW` are applied to the plot containing the w-data. The
         options specified in `optionsZ` are applied to the plot
         containing the z-data.
         
         #########
         #(w)#(x)#
         #########
         #(y)#(z)#
         #########
    
    >>> plot([[DateSeries(w), None],\
    >>>       [DateSeries(y), DateSeries(z)]])
    >>>
    out: Plots the contents of w, y and z in different panels. The
         panels are arranged in a 2 by 2 grid. The upper right panel is
         not populated.
         
         #########
         #(w)#   #
         #########
         #(y)#(z)#
         #########
    """
    #Handle 0D case
    if not isinstance(args, list):
        if isinstance(args, (DateSeries, tuple)):
            args = [[args]]
        elif isinstance(args, tuple):
            fig, axs = args[0].plot(**kwargs)
            msg = 'The argument to `plot` must be either a list '
            raise TypeError(msg)
    
    #Handle 1D case or case where the input is only partially 2D
    is_list = [isinstance(pt, list) for pt in args]
    if not all(is_list):
        if any(is_list): #Partially 2D
            tmp = []
            for i, pt in enumerate(args):
                if is_list[i]:
                    tmp.append(pt)
                else:
                    tmp.append([pt])
            args = tmp
        else:
            if default_orientation.lower() == 'v':
                args = [[pt] for pt in args]
            elif default_orientation.lower() == 'h':
                args = [args]
            else:
                raise RuntimeError('Bad option')
    
    #Create 2D array-like structure
    max_len = max([len(pt) for pt in args])
    tmp = []
    for pt in args:
        if len(pt) != max_len:
            tmp2 = []
            for i in range(max_len):
                if i < len(pt):
                    tmp2.append(pt[i])
                else:
                    tmp2.append(None)
            tmp.append(tmp2)
        else:
            tmp.append(pt)
    args = tmp
    shape = (len(args), max_len)
    rows = shape[0]
    cols = shape[1]
    
    #Create figure and axes
    fig, axs = plt.subplots(nrows=rows,
                            ncols=cols)
    if rows == 1:
        if cols == 1:
            axs = [[axs]]
        else:
            axs = [axs]
    else:
        if cols == 1:
            axs = [[pt] for pt in axs]
    
    #Check if all array-entries are atomic pieces. If so give all of
    #them basic options.
    rows_tmp = []
    for i in range(rows):
        cols_tmp = []
        for j in range(cols):
            curr = args[i][j]
            if curr is None:
                cols_tmp.append(None)
            else:
                base_options = {'fig': fig, 'ax': axs[i][j]}
                if isinstance(curr, tuple):
                    if len(curr) == 2:
                        if isinstance(curr[0], DateSeries):
                            if isinstance(curr[1], DateSeries):
                                cols_tmp.append((OptionWrapper(curr[0], base_options),
                                                OptionWrapper(curr[1], base_options)))
                            elif isinstance(curr[1], tuple):
                                pt1 = OptionWrapper(curr[0], base_options)
                                obj = curr[1][0]
                                opt = curr[1][1]
                                opt.update(base_options)
                                pt2 = OptionWrapper(obj, opt)
                                cols_tmp.append((pt1, pt2))
                            else:
                                obj = curr[0]
                                opt = curr[1]
                                opt.update(base_options)
                                cols_tmp.append((OptionWrapper(obj, opt),))
                        else:
                            obj = curr[0][0]
                            opt = curr[0][1]
                            opt.update(base_options)
                            if isinstance(curr[1], DateSeries):
                                pt1 = OptionWrapper(obj, opt)
                                pt2 = OptionWrapper(curr[1], base_options)
                                cols_tmp.append((pt1, pt2))
                            elif isinstance(curr[1], tuple):
                                pt1 = OptionWrapper(obj, opt)
                                obj2 = curr[1][0]
                                opt2 = curr[1][1]
                                opt2.update(base_options)
                                pt2 = OptionWrapper(obj2, opt2)
                                cols_tmp.append((pt1, pt2))
                            else:
                                raise RuntimeError
                    else:
                        tmp = []
                        for pt in curr:
                            if isinstance(pt, tuple):
                                obj = pt[0]
                                opt = pt[1]
                                opt.update(base_options)
                                tmp.append(OptionWrapper(obj, opt))
                            else:
                                tmp.append(OptionWrapper(pt, base_options))
                        cols_tmp.append(tuple(tmp))
                elif isinstance(curr, DateSeries):
                    cols_tmp.append((OptionWrapper(curr, base_options),))
                else:
                    raise TypeError
        rows_tmp.append(cols_tmp)
    args = rows_tmp
    
    #Do the plotting
    for i in range(rows):
        for j in range(cols):
            if args[i][j] is not None:
                for pt in args[i][j]:
                    _1, _2 = pt.plot()
                if grid:
                    axs[i][j].grid()
                if legend:
                    axs[i][j].legend()
            else:
                axs[i][j].set_axis_off()
    
    if not store == False:
        if store == True:
            fig.savefig('plot.png')
        else:
            fig.savefig(store)
    
    if show:
        fig.show()
    
    return fig, axs
