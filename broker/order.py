import datetime
from ..depot import Position
from ..feed import CandleFeed
from .constraints import BaseConstraint, BaseLimit, BaseStop

class OrderAction(object):
    BUY_LONG = 0
    SELL_LONG = 1
    BUY_SHORT = 2
    SELL_SHORT = 3
    def __init__(self, order_action):
        if isinstance(order_action, int):
            if order_action in [self.BUY_LONG, self.SELL_LONG,
                              self.BUY_SHORT, self.SELL_SHORT]:
                self.order_action = order_action
            else:
                raise ValueError
        elif isinstance(order_action, str):
            try:
                self.order_action = getattr(self, order_action.upper())
            except:
                raise ValueError
        elif isinstance(order_action, self.__class__):
            self.order_action = order_action.order_action
        else:
            raise TypeError
    
    def _check_action(self, arg=None, target=None):
        if target is None:
            target = []
        if arg is None:
            try:
                arg = self.order_action
            except AttributeError:
                msg = 'An OrderAction must be provided.'
                raise ValueError
        return arg in target
    
    def isBuy(self, arg=None):
        return self._check_action(arg=arg,
                                  target=[self.BUY_LONG, self.BUY_SHORT])
    
    def isSell(self, arg=None):
        return self._check_action(arg=arg,
                                  target=[self.SELL_LONG, self.SELL_SHORT])
    
    def isLong(self, arg=None):
        return self._check_action(arg=arg,
                                  target=[self.BUY_LONG, self.SELL_LONG])
    
    def isShort(self, arg=None):
        return self._check_action(arg=arg,
                                  target=[self.BUY_SHORT, self.SELL_SHORT])
    
    def isBuyLong(self, arg=None):
        return self._check_action(arg=arg,
                                  target=[self.BUY_LONG])
    
    def isSellLong(self, arg=None):
        return self._check_action(arg=arg,
                                  target=[self.SELL_LONG])
    
    def isBuyShort(self, arg=None):
        return self._check_action(arg=arg,
                                  target=[self.BUY_SHORT])
    
    def isSellShort(self, arg=None):
        return self._check_action(arg=arg,
                                  target=[self.SELL_SHORT])

class GroupAction(object):
    ONE_CANCELS_ALL = 0
    def __init__(self, order_action):
        if isinstance(order_action, int):
            if order_action in [self.ONE_CANCELS_ALL]:
                self.order_action = order_action
            else:
                raise ValueError
        elif isinstance(order_action, str):
            try:
                self.order_action = getattr(self, order_action.upper())
            except:
                raise ValueError
        elif isinstance(order_action, self.__class__):
            self.order_action = order_action.order_action
        else:
            raise TypeError
    
    def _check_action(self, arg=None, target=None):
        if target is None:
            target = []
        if arg is None:
            try:
                arg = self.order_action
            except AttributeError:
                msg = 'An OrderAction must be provided.'
                raise ValueError
        return arg in target
    
    def isOneCancelsAll(self, args=None):
        return self._check_action(arg=arg,
                                  target=[self.ONE_CANCELS_ALL])

class OrderStatus(object):
    IDLE = 0
    ACTIVE = 1
    CANCELLED = 2
    PARTIALLY_FILLED = 3
    FILLED = 4
    
    ALLOWED_TRANSITIONS = {IDLE: [IDLE, ACTIVE, CANCELLED],
                           ACTIVE: [IDLE, ACTIVE, CANCELLED, PARTIALLY_FILLED, FILLED],
                           CANCELLED: [CANCELLED],
                           PARTIALLY_FILLED: [CANCELLED, PARTIALLY_FILLED, FILLED],
                           FILLED: [FILLED]}
    
    def __init__(self, status):
        if isinstance(status, int):
            if status in [self.IDLE, self.ACTIVE, self.CANCELLED,
                          self.PARTIALLY_FILLED, self.FILLED]:
                self.order_status = status
            else:
                raise ValueError('Got integer of value {}'.format(status))
        elif isinstance(status, str):
            try:
                self.order_status = getattr(self, status.upper())
            except:
                raise ValueError
        elif isinstance(status, OrderStatus):
            self.order_status = status.order_status
        else:
            raise TypeError('Received {} of type {}'.format(status, type(status)))
    
    def __str__(self):
        names = {self.IDLE: 'idle',
                 self.ACTIVE: 'active',
                 self.CANCELLED: 'cancelled',
                 self.PARTIALLY_FILLED: 'partially filled',
                 self.FILLED: 'filled'}
        return f'<OrderStatus: {names[self.order_status]}>'
    
    def __repr__(self):
        return f'<OrderStatus({self.order_status})>'
    
    def _check_status(self, arg=None, target=None):
        if target is None:
            target = []
        if arg is None:
            try:
                arg = self.order_status
            except AttributeError:
                msg = 'An OrderStatus must be provided.'
                raise ValueError(msg)
        return arg in target
    
    def isActive(self, arg=None):
        return self._check_status(arg=arg, target=[self.ACTIVE,
                                                   self.PARTIALLY_FILLED])
    
    def isClosed(self, arg=None):
        return self._check_status(arg=arg, target=[self.CANCELLED,
                                                   self.FILLED])
    
    def isIdle(self, arg=None):
        return self._check_status(arg=arg, target=[self.IDLE])
    
    def isCancelled(self, arg=None):
        return self._check_status(arg=arg, target=[self.CANCELLED])
    
    def isPartiallyFilled(self, arg=None):
        return self._check_status(arg=arg, target=[self.PARTIALLY_FILLED])
    
    def isFilled(self, arg=None):
        return self._check_status(arg=arg, target=[self.FILLED])
    
    def transition_allowed(self, *new_status):
        if len(new_status) > 1:
            old_status = OrderStatus(new_status[0])
            new_status = OrderStatus(new_status[1])
        elif len(new_status) == 1 and hasattr(self, 'order_status'):
            old_status = self
            new_status = OrderStatus(new_status)
        else:
            raise RuntimeError
        allow = self.ALLOWED_TRANSITIONS[old_status.order_status]
        return new_status.order_status in allow
    
    def transition(self, *new_status):
        if len(new_status) > 1:
            old_status = OrderStatus(new_status[0])
            new_status = OrderStatus(new_status[1])
        elif len(new_status) == 1 and hasattr(self, 'order_status'):
            old_status = self
            new_status = OrderStatus(new_status[0])
        else:
            raise RuntimeError
        allow = self.ALLOWED_TRANSITIONS[old_status.order_status]
        transition_okay = new_status.order_status in allow
        if transition_okay:
            old_status.order_status = new_status.order_status
        return transition_okay

class BaseOrder(object):
    def __init__(self, target, action, limit=None, stop=None,
                 quantity=None, all_or_nothing=True, good_until=None):
        self.target = target
        self.candle_feed = self.target if isinstance(self.target, CandleFeed) else self.target.candle_feed
        self.action = OrderAction(action)
        self.limit = limit
        self.stop = stop
        self.quantity = quantity
        self.initial_quantity = self.quantity
        assert isinstance(all_or_nothing, bool)
        self.all_or_nothing = all_or_nothing
        self.good_until = good_until
        self.status = OrderStatus('idle')
    
    @property
    def target(self):
        return self._target
    
    @target.setter
    def target(self, target):
        if isinstance(target, (CandleFeed, Position)):
            self._target = target
        else:
            raise TypeError
    
    @property
    def candle_feed(self):
        return self._candle_feed
    
    @candle_feed.setter
    def candle_feed(self, candle_feed):
        if isinstance(candle_feed, CandleFeed):
            self._candle_feed = candle_feed
        elif isinstance(candle_feed, Position):
            self._candle_feed = candle_feed.candle_feed
        else:
            raise RuntimeError
    
    @property
    def quantity(self):
        return self._quantity
    
    @quantity.setter
    def quantity(self, quantity):
        if quantity is None:
            self._quantity = None
        elif isinstance(quantity, (int, float)):
            if quantity < 0:
                raise ValueError
            self._quantity = quantity
        else:
            raise TypeError
    
    @property
    def good_until(self):
        return self._good_until
    
    @good_until.setter
    def good_until(self, good_until):
        if good_until is None:
            self._good_until = good_until
        elif isinstance(good_until, datetime.datetime):
            self._good_until = good_until
        else:
            raise TypeError
    
    def update(self):
        if self.good_until is not None:
            if self.good_until < self.candle_feed.dateindex:
                self.update_status(OrderStatus.CANCELLED)
        self.limit.update()
        self.stop.update()
        candle = self.candle_feed.value
        try:
            limit_okay = self.limit.check(candle)
        except:
            limit_okay = self.limit is None
        try:
            stop_okay = self.stop.check(candle)
        except:
            stop_okay = self.stop is None
        
        if limit_okay and stop_okay and not self.isActive():
            trans_okay = self.status.transition(OrderStatus.ACTIVE)
            if not trans_okay:
                msg = 'Transition not allowed.'
                raise RuntimeError(msg)
    
    def update_status(self, status):
        return self.status.transition(status)
    
    def cancel(self):
        self.update_status(OrderStatus.CANCELLED)
    
    def fill(self, quantity):
        """The broker calls this function when attempting to fill the
        order.
        
        Arguments
        ---------
        quantity : None or int or float
            The number of shares that the broker is targeting.
            In the case that the quantity asked for by the order is
            None, this argument may be None. This notifies the broker if
            the order accepts this allocation of shares.
        
        Returns
        -------
        bool:
            True if the order may be filled in the attempted intended
            quantity.
        """
        if self.quantity is None:
            if quantity is None:
                return self.update_status(OrderStatus.FILLED)
            return False
        if quantity is None:
            return False
        if quantity > self.quantity:
            return False
        if quantity < 1:
            return False
        if quantity < self.quantity:
            if self.all_or_nothing:
                return False
            self.quantity -= quantity
            return self.update_status(OrderStatus.PARTIALLY_FILLED)
        self.quantity = 0
        return self.update_status(OrderStatus.FILLED)
    
    def isBuy(self):
        return self.action.isBuy()
    
    def isSell(self):
        return self.action.isSell()
    
    def isLong(self):
        return self.action.isLong()
    
    def isShort(self):
        return self.action.isShort()
    
    def isBuyLong(self):
        return self.action.isBuyLong()
    
    def isSellLong(self):
        return self.action.isSellLong()
    
    def isBuyShort(self):
        return self.action.isBuyShort()
    
    def isSellShort(self):
        return self.action.isSellShort()
    
    def isActive(self):
        return self.status.isActive()
    
    def isClosed(self):
        return self.status.isClosed()
    
    def isIdle(self):
        return self.status.isIdle()
    
    def isCancelled(self):
        return self.status.isCancelled()
    
    def isPartiallyFilled(self):
        return self.status.isPartiallyFilled()
    
    def isFilled(self):
        return self.status.isFilled()

class BaseOrderGroup(object):
    def __init__(self, group_action, orders=None):
        self.group_action = group_action
        self.orders = orders
    
    @property
    def group_action(self):
        return self._group_action
    
    @group_action.setter
    def group_action(self, group_action):
        self._group_action = GroupAction(group_action)
    
    @property
    def orders(self):
        return self._orders
    
    @orders.setter
    def orders(self, orders):
        if orders is None:
            self._orders = []
        elif isinstance(orders, BaseOrder):
            self._orders = [orders]
        elif all([isinstance(order, (BaseOrder, BaseOrderGroup)) for order in orders]):
            self._orders = orders
        else:
            raise TypeError
            
class OneCancelsAllOrderGroup(BaseOrderGroup):
    def __init__(self, orders=None):
        super().__init__(group_action=GroupAction('ONE_CANCELS_ALL'),
                         orders=orders)

class BuyLongOrder(BaseOrder):
    def __init__(self, target, quantity, limit=None, stop=None,
                 action_group=None, all_or_nothing=True,
                 good_until=None):
        if not isinstance(limit, BaseConstraint):
            limit = BaseLimit(price=limit, limit_type='long')
        if not isinstance(stop, BaseConstraint):
            stop = BaseStop(price=stop, stop_type='long')
        
        super().__init__(target, OrderAction.BUY_LONG, limit=limit,
                         stop=stop, quantity=quantity,
                         all_or_nothing=all_or_nothing,
                         good_until=good_until)

class SellLongOrder(BaseOrder):
    def __init__(self, target, quantity, limit=None, stop=None,
                 action_group=None, all_or_nothing=True,
                 good_until=None):
        if not isinstance(limit, BaseConstraint):
            limit = BaseLimit(price=limit, limit_type='short')
        if not isinstance(stop, BaseConstraint):
            stop = BaseStop(price=stop, stop_type='short')
        
        super().__init__(target, OrderAction.SELL_LONG, limit=limit,
                         stop=stop, quantity=quantity,
                         all_or_nothing=all_or_nothing,
                         good_until=good_until)
