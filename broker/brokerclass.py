import warnings
import datetime
from .. import depot as dep
from . import orderhistory as ordhist
from . import brokercost as bk
from ..types.priorityQueue import PriorityQueue
from ..feed import CandleFeed
from . import broker_filling_strategy as bf
from ..depot import Position
from .order import BaseOrder


"""
Broker commands
-buy(candle_feed, amount, price=None)
-sell(position, amount, price=None)
-cancel(orderid, {more orderids})
-buy_cancel(candle_feed, amount, price=None, orderids=None)
-sell_cancel(candle_feed, amount, price=None, orderids=None)
-adjust_amount(orderid, amount_diff)
-
"""


class Broker(object):
    def __init__(self, depots=None, active_depot=None, history=None,
                 broker_cost=None, tax=None, filling_strategy=None):
        self.depots = depots
        self.active_depot = active_depot
        #TODO: Replace the order history with a non-base class once implemented.
        self.history = history if history is not None else ordhist.BaseOrderHistory()
        self.broker_cost = broker_cost if broker_cost is not None else bk.NoBrokerCost()
        self.filling_strat = filling_strategy if filling_strategy is not None else bf.SimpleFillingStrategy()
        self.order_queue = PriorityQueue()
        self.orders = {}
        self.current_dateindex = None
        self.candle_feeds = {}
    
    def __contains__(self, item):
        if isinstance(item, dep.Depot):
            return item in self.depots
        elif isinstance(item, CandleFeed):
            return item in list(self.candle_feeds.values())
        elif isinstance(item, BaseOrder):
            in_order_q = item in self.order_queue
            in_orders = item in list(self.orders.value())
            return in_order_q or in_orders
        else:
            raise TypeError
    
    @property
    def max_order_id(self):
        order_ids = list(self.orders.keys())
        if len(order_ids) == 0:
            return -1
        else:
            return max(order_ids)
    
    @property
    def min_dateindex(self):
        return max([cf.min_dateindex for cf in self.candle_feeds.values()])
    
    @property
    def max_dateindex(self):
        return max([cf.max_dateindex for cf in self.candle_feeds.values()])
    
    @property
    def depots(self):
        return self._depots
    
    @depots.setter
    def depots(self, depots):
        self._depots = {}
        if depots is None:
            return
        elif isinstance(depots, dep.Depot):
            self.add_depot(depots)
            return
        else:
            msg = 'To set the depots at the Broker, depots must be '
            msg += 'provided as part of an iterable or as a single '
            msg += 'depot instance.'
            try:
                depots = list(depots)
                if all([isinstance(depot, dep.Depot) for depot in depots]):
                    for depot in depots:
                        self.add_depot(depot)
                else:
                    raise ValueError(msg)
            except:
                raise TypeError(msg)
    
    def get_depot_name(self, depot):
        if isinstance(depot, str):
            return depot
        elif isinstance(depot, dep.Depot):
            for key, val in self.depots.items():
                if val == depot:
                    return key
            return depot.name
        elif depot is None:
            return self.active_depot
        else:
            return None
    
    def get_depot(self, depot):
        return self.depots[self.get_depot_name(depot)]
    
    def add_depot(self, depot, name=None):
        if isinstance(depot, dep.Depot):
            if name is None:
                name = depot.name
            if name in self.depots:
                msg = f'Trying to add a Depot with name {name} to the '
                msg += 'broker. Names need to be unique and there is '
                msg += 'already a Depot with the same name requistered '
                msg += 'with this Broker.'
                raise ValueError(msg)
            self.depots[name] = depot
            self.active_depot = name
        else:
            msg = 'The provided Depot must be a sub-class of '
            msg += f'PyTrest.depot.BaseDepot. Got {type(depot)} instead.'
            raise ValueError(msg)
    
    def remove_depot(self, depot):
        if not (isinstance(depot, str) or isinstance(depot, dep.Depot)):
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
        depot_fees = self.broker_cost.on_date(self.current_dateindex)
        if depot_fees > 0:
            rem_depots = []
            for key, depot in self.depots.items():
                exe = depot.pay_broker(depot_fees, msg='Broker: Depot cost')
                if not exe:
                    depot.save()
                    rem_depots.append(key)
                    msg = 'Could not pay the required cost for the depot'
                    msg += ' {}. Removed it from the Broker.'
                    msg = msg.format(key)
                    warnings.warn(msg, RuntimeWarning)
            for key in rem_depots:
                self.depots.pop(key)
    
    def depots_to_current_date(self):
        for depot in self.depots.values():
            depot.update_dateindex(self.current_dateindex)
    
    def advance_time(self, timedelta=None, process_order_queue=True):
        if process_order_queue:
            self.process_order_queue()
        if timedelta is None:
            next_dates = []
            for cf in self.candle_feeds.values():
                date = cf.next_date()
                if date > self.current_dateindex:
                    next_dates.append(date)
            if len(next_dates) == 0:
                raise StopIteration
            self.current_dateindex = min(next_dates)
        else:
            if not isinstance(timedelta, datetime.timedelta):
                raise TypeError
            self.current_dateindex += timedelta
        self.candle_feeds_to_current_date()
        self.depots_to_current_date()
    
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
        cost = self.broker_cost.on_order_comission(order)
        exe = self.depots[depot].pay_broker(cost, msg='Broker: Order comission')
        if not exe:
            msg = 'Order was not accepted by the Broker because the '
            msg += 'costs could not be covered by the Depot {}.'
            msg = msg.format(depot)
            warnings.warn(msg, RuntimeWarning)
        else:
            self.order_queue.enqueue((depot, order), priority=dateindex)
    
    def process_order_queue(self):
        next_queue = PriorityQueue()
        for (depot, order) in self.order_queue:
            order.update()
            self.execute_order(depot, order)
            if order.isCancelled():
                cancel_cost = self.broker_cost.on_order_cancel(order)
                exe = self.depots[depot].pay_broker(cancel_cost, msg='Broker: Order cacelled')
                if not exe:
                    msg = 'Could not pay broker to cancel the order!'
                    warnings.warn(msg, RuntimeWarning)
            if not order.isClosed():
                next_queue.enqueue((depot, order),
                                   priority=self.current_dateindex)
        self.order_queue = next_queue
    
    def cancel_order(self, depot, order):
        depot = self.get_depot(depot)
        cost = self.broker_cost.on_order_cancel(order)
        exe = depot.pay_broker(cost, msg='Broker: Cancelled order')
        if not exe:
            warnings.warn('Insufficient funds to cancel order.', RuntimeError)
        order.cancel()
    
    def execute_order(self, depot, order):
        depot = self.get_depot(depot)
        price, quantity = self.filling_strat.execute_order(order)
        
        if quantity is None or quantity == 0:
            return
        if quantity < order.quantity and order.all_or_nothing:
            self.cancel_order(depot, order)
            return
        cost = self.broker_cost.on_order_execution(order, price)
            
        if isinstance(order.target, Position):
            pos = order.target
        else:
            pos = depot.get_base_position(order.target)
        
        if pos not in depot:
            depot.portfolio.add_position(pos)
        
        if order.isBuyLong():
            if not price * quantity + cost <= depot.cash:
                warnings.warn('Insufficient funds to fulfill buy long order.')
                return
            exe = depot.pay_broker(cost, msg='Broker: On order execution')
            if not exe:
                return
            depot.increase_position_size(pos, amount=quantity, price=price)
        elif order.isSellLong():
            depot.reduce_position_size(pos, amount=quantity, price=price)
            exe = depot.pay_broker(cost, msg='Broker: On order execution')
            if not exe:
                raise RuntimeError('Could not pay broker after executing sell order.')
        elif order.isBuyShort():
            depot.reduce_position_size(pos, amount=quantity, price=price)
        elif order.isSellShort():
            depot.increase_position_size(pos, amount=quantity, price=price)
        order.fill(quantity)
