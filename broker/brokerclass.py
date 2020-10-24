import warnings
import datetime
from .. import depot as dep
from . import orderhistory as ordhist
from . import brokercost as bk
from ..types.priorityQueue import PriorityQueue
from ..feed import CandleFeed

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
                 broker_cost=None, tax=None):
        self.depots = depots
        self.active_depot = active_depot
        #TODO: Replace the order history with a non-base class once implemented.
        self.history = history if history is not None else ordhist.BaseOrderHistory()
        self.broker_cost = broker_cost if broker_cost is not None else bk.NoBrokerCost()
        self.order_queue = PriorityQueue()
        self.orders = {}
        self.current_dateindex = None
        self.candle_feeds = {}
        
        self.order_function_dict = {"buy": self.process_buy_order,
                                    "sell": self.process_sell_order,
                                    "cancel": self.process_cancel_order,
                                    "buy_cancel": self.process_buy_cancel_order,
                                    "sell_cancel": self.process_sell_cancel_order,
                                    "adjust_amount": self.process_adjust_amount_order,
                                    "drop_from_queue": self.process_drop_from_queue_order
                                    }
        return
    
    @property
    def max_order_id(self):
        order_ids = list(self.orders.keys())
        if len(order_ids) == 0:
            return -1
        else:
            return max(order_ids)
    
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
            depot.curr_dateindex = self.current_dateindex
    
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
            eval_order = order.evaluate()
            if eval_order[0] == 'idle':
                next_queue.enqueue((depot, order),
                                   priority=self.current_dateindex)
            else:
                if order.order_id is -1:
                    order_id = self.max_order_id + 1
                    order.order_id = order_id
                    self.orders[order_id] = order
                else:
                    order_id = order.order_id
                    if order_id in self.orders:
                        if not order == self.orders[order_id]:
                            msg = 'Found existing order with the same '
                            msg += 'ID. Will assign a new, unique ID.'
                            warnings.warn(msg, RuntimeWarning)
                            order_id = self.max_order_id + 1
                            order.order_id = order_id
                            self.orders[order_id] = order
                    else:
                        self.orders[order_id] = order
                eval_order[1].update({'order_id': order_id})
                fill_status = self.order_function_dict[eval_order[0]](depot, order,
                                                                      **eval_order[1])
                order.status = fill_status
                #self.history.add(self.current_dateindex, depot, order)
        self.order_queue = next_queue
    
    def cancel_order(self, depot, order_id):
        order = self.orders[order_id]
        order.status = 'canceled'
        order.command = 'drop_from_queue'
        order.arguments.update({'order_status': order.status})
        cost = self.broker_cost.on_order_cancel(self.order[order_id])
        exe = depot.pay_broker(cost, msg='Broker: Cancel order {}'.format(order_id))
        if not exe:
            msg = 'Depot {} did not contain sufficient funds to pay the'
            msg += ' broker for canceling the order {}. The depot was '
            msg += 'therefore removed from the broker.'
            msg = msg.format(depot, order_id)
            warnings.warn(msg, RuntimeWarning)
            self.remove_depot(depot)
    
    ##################
    #Order processing#
    ##################
    def process_buy_order(self, depot, order, **kwargs):
        depot = self.get_depot_name(depot)
        cf = kwargs.get('candle_feed', None)
        if cf is None:
            msg = 'No CandleFeed provided to this buy order. Will cancel'
            msg += ' the order.'
            warnings.warn(msg, RuntimeWarning)
            self.cancel_order(depot, kwargs.get('order_id'))
            return "canceled"
        if cf not in list(self.candle_feeds.values()):
            msg = 'Trying to buy from unknown CandleFeed {}.'.format(cf)
            msg += ' Order is canceled.'
            warnings.warn(msg, RuntimeWarning)
            self.cancel_order(depot, kwargs.get('order_id'))
            return "canceled"
        price = kwargs.get('price', cf.value.high)
        amount = kwargs.get('amount', None)
        if not isinstance(amount, int):
            msg = 'Could not interpret the amount requested by the buy-'
            msg += 'order. Will cancel the order.'
            warnings.warn(msg, RuntimeWarning)
            self.cancel_order(depot, kwargs.get('order_id'))
            return "canceled"
        cost = self.broker_cost.on_order_execution(order, price*amount)
        if self.depots[depot].cash < amount * price + cost:
            msg = 'The targeted depot {} did not provide enough funds '
            msg += 'to cover the expenses for the position and the '
            msg += 'mandatory broker fee. Will cancel the order.'
            warnings.warn(msg, RuntimeWarning)
            self.cancel_order(depot, kwargs.get('order_id'))
            return "canceled"
        if cost > 0:
            exe = self.depots[depot].pay_broker(cost, 'Broker: Order execution {}'.format(kwargs.get('order_id')))
        else:
            exe = True
        
        if not exe:
            raise RuntimeError
        
        self.depots[depot].open_position(cf, dateindex=cf.dateindex,
                                         amount=amount, price=price,
                                         position_type=kwargs.get('position_type', 'long'))
        return "filled"
    
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
    
    def process_drop_from_queue_order(self, depot, **kwargs):
        return kwargs.get('order_status', "failed")
