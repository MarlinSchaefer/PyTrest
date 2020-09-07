import PyTrest.depot as dep
import orderhistory as ordhist
import brokercost as bk
from PyTrest.types import PriorityQueue
from PyTrest.feed import CandleFeed

"""
Broker commands
-buy(candle_feed, amount, price=None)
-sell(candle_feed, amount, price=None)
-cancel(orderid, {more orderids})
-buy_cancel(candle_feed, amount, price=None, orderids=None)
-sell_cancel(candle_feed, amount, price=None, orderids=None)
-adjust_amount(orderid, amount_diff)
-
"""

class Broker(object):
    def __init__(self, depots=None, active_depot=None, history=None,
                 broker_cost=None):
        self.depots = depots
        self.active_depot = active_depot
        #TODO: Replace the order history with a non-base class once implemented.
        self.history = history if history is not None else ordhist.BaseOrderHistory()
        #TODO: Replace broker cost with a non-base class once implemented.
        self.broker_cost = bk.BaseBrokerCost()
        self.order_queue = PriorityQueue()
        self.current_dateindex = None
        self.candle_feeds = {}
        
        order_function_dict = {"buy": self.process_buy_order,
                               "sell": self.process_sell_order,
                               "cancel": self.process_cancel_order,
                               "buy_cancel": self.process_buy_cancel_order,
                               "sell_cancel": self.process_sell_cancel_order,
                               "adjust_amount":self.process_adjust_amount_order
                               }
        return
    
    @property
    def depots(self):
        return self._depots
    
    @depots.setter
    def depots(self, depots):
        self._depot = {}
        if depots is None:
            return
        elif isinstance(depots, dep.BaseDepot):
            self.add_depot(depots)
            return
        else:
            msg = 'To set the depots at the Broker, depots must be '
            msg += 'provided as part of an iterable or as a single '
            msg += 'depot instance.'
            try:
                depots = list(depots)
                if all([isinstance(depot, dep.BaseDepot) for depot in depots]):
                    for depot in depots:
                        self.add_depot(depot)
                else:
                    raise ValueError(msg)
            except:
                raise TypeError(msg)
    
    def get_depot_name(self, depot):
        if isinstance(depot, str):
            return depot
        elif isinstance(depot, dep.BaseDepot):
            for key, val in self.depots.items():
                if val == depot:
                    return key
            return depot.name
        elif depot is None:
            return self.active_depot
        else:
            return None
    
    def add_depot(self, depot, name=None):
        if isinstance(depot, dep.BaseDepot):
            if name is None:
                name = depot.name
            if name in self.depots:
                msg = f'Trying to add a Depot with name {name} to the '
                msg += 'broker. Names need to be unique and there is '
                msg += 'already a Depot with the same name requistered '
                msg += 'with this Broker.'
                raise ValueError(msg)
            self.depot[name] = depot
            self.active_depot = name
        else:
            msg = 'The provided Depot must be a sub-class of '
            msg += f'PyTrest.depot.BaseDepot. Got {type(depot)} instead.'
            raise ValueError(msg)
    
    def remove_depot(self, depot):
        if not (isinstance(depot, str) or isinstance(depot, dep.BaseDepot)):
            msg = 'Depots may only be removed by providing the name as '
            msg += f'a string or the Depot itself. Got {type(depot)} '
            msg += 'instead.'
            raise ValueError(msg)
        name = self.get_depot_name(depot)
        if name is None:
            return None
        if name not in self.depots:
            return None
        return self.depots.pop(name)
    
    def change_active_depot(self, depot):
        if depot is None:
            return
        name = self.get_depot_name(depot)
        if name is None:
            msg = 'Could not find a depot corresponding to the given '
            msg += 'input.'
            raise KeyError(msg)
        self.active_depot = name
    
    def register_candle_feed(self, name, candle_feed):
        if not isinstance(candle_feed, CandleFeed):
            raise TypeError
        if name not in self.candle_feeds:
            if self.current_dateindex is None:
                self.current_dateindex = candle_feed.index[0]
            candle_feed.set_head_or_prior(self.current_dateindex)
            self.candle_feeds[name] = candle_feed
        else:
            return ValueError
    
    def get_candle_feed(self, name):
        return self.candle_feeds[name]
    
    def candle_feeds_to_current_date(self):
        for cf in self.candle_feeds.values():
            cf.set_head_or_prior(self.current_dateindex)
    
    def advance_time(self, timedelta=None, process_order_queue=True):
        if process_order_queue:
            self.process_order_queue()
        if timedelta is None:
            next_dates = []
            for cf in self.candle_feeds.values():
                date = cf.next_date()
                if date > self.current_dateindex:
                    next_dates.append(date)
            if len(next_date) == 0:
                raise StopIteration
            self.current_dateindex = min(next_dates)
        else:
            if not isinstance(timedelta, datetime.timedelta):
                raise TypeError
            self.current_dateindex += timedelta
        self.candle_feeds_to_current_date()
    
    def set_time(self, dateindex):
        for cf_name, cf in self.candle_feeds.items():
            if cf.min_dateindex > dateindex:
                msg = 'CandleFeed {} does not contain data before {}.'
                msg = msg.format(cf_name, cf.min_dateindex)
                raise RuntimeError(msg)
            cf.set_head_or_prior(dateindex)
        self.current_dateindex = dateindex
    
    def submit_order(self, order, depot=None, dateindex=None):
        """Submit an order to the Broker.
        
        Arguments
        ---------
        order : PyTrest.broker.order
            The order that is placed.
        depot : {str or PyTrest.depot or None, None}
            The depot on which the order is based. (Cash is taken out of
            that depot and positions are added to the depot.) If set to
            None the currently active depot will be used.
        dateindex : {datetime or None, None}
            Submit the order at a specific datetime. This can be used to
            control the sequence in which orders are processed.
        
        Returns
        -------
        filled : bool
            True if the order could be filled, False if it could not be
            filled.
        """
        depot = self.get_depot_name(depot)
        self.order_queue.enqueue((depot, order), priority=dateindex)
    
    def process_order_queue(self):
        next_queue = PriorityQueue()
        for (depot, order) in self.order_queue:
            eval_order = order.evaluate()
            if eval_order[0] == 'idle':
                next_queue.enqueue((depot, order),
                                   priority=self.current_dateindex)
            else:
                fill_status = self.order_function_dict[eval_order[0]](depot,
                                                                      **eval_order[1])
                order.status = fill_status
                self.history.add(self.current_dateindex, depot, order)
        self.order_queue = next_queue
    
    ##################
    #Order processing#
    ##################
    def process_buy_order(self, depot, **kwargs):
        return "failed"
    
    def process_sell_order(self, depot, **kwargs):
        return "failed"
    
    def process_cancel_order(self, depot, **kwargs):
        return "failed"
    
    def process_buy_cancel_order(self, depot, **kwargs):
        return "failed"
    
    def process_sell_cancel_order(self, depot, **kwargs):
        return "failed"
    
    def process_adjust_amount_order(self, depot, **kwargs):
        return "failed"
