import numpy as np
import datetime
from PyTrest.currency import Money

class BaseBrokerCost(object):
    def __init__(self, currency='USD'):
        self.zero = Money(0., currency=currency)
    
    def on_order_comission(self, order):
        raise NotImplementedError
    
    def on_order_execution(self, order, price):
        raise NotImplementedError
    
    def on_order_cancel(self, order):
        raise NotImplementedError
    
    def on_date(self, dateindex):
        raise NotImplementedError

class NoBrokerCost(BaseBrokerCost):
    def __init__(self, currency='USD'):
        super().__init__(currency=currency)
    
    @property
    def currency(self):
        return self.zero.currency
    
    def on_order_comission(self, order):
        return self.zero
    
    def on_order_execution(self, order, price):
        return self.zero
    
    def on_order_cancel(self, order):
        return self.zero
    
    def on_date(self, dateindex):
        return self.zero

class FixedOrderFee(BaseBrokerCost):
    def __init__(self, fee=None, currency='USD'):
        self.fee = Money(fee, currency=currency)
        super().__init__(currency=self.currency)
    
    @property
    def currency(self):
        return self.fee.currency
    
    def on_order_comission(self, order):
        return self.zero
    
    def on_order_execution(self, order, price):
        return self.fee
    
    def on_order_cancel(self, order):
        return self.fee
    
    def on_date(self, dateindex):
        return self.zero

class PercentageFee(BaseBrokerCost):
    def __init__(self, percentage, min_fee=None, max_fee=None,
                 currency='USD', depot_cost=None,
                 depot_cost_interval='monthly'):
        self.perc = percentage
        self.min_fee = Money(min_fee, currency=currency)
        if max_fee is None:
            self.max_fee = Money(np.inf, currency=self.currency)
        else:
            self.max_fee = self.min_fee.as_own_currency(Money(max_fee,
                                                              currency=self.currency))
        self.depot_cost = self.min_fee.as_own_currency(Money(depot_cost,
                                                             currency=self.currency))
        if depot_cost_interval.lower() in ['monthly', 'yearly']:
            self.depot_cost_interval = depot_cost_interval.lower()
        else:
            msg = 'depot_cost_interval must be either `monthly` or '
            msg += '`yearly`.'
            raise ValueError(msg)
        self.last_depot_cost = None
        super().__init__(currency=self.currency)
    
    @property
    def currency(self):
        return self.min_fee.currency
    
    def on_order_comission(self, order):
        return self.zero
    
    def on_order_execution(self, order, price):
        perc_fee = Money(price * self.perc, currency=self.currency)
        return min(self.max_fee, min(self.min_fee, perc_fee))
    
    def on_order_cancel(self, order):
        return self.min_fee
    
    def on_date(self, dateindex):
        if self.depot_cost_interval == 'monthly':
            if self.last_depot_cost is None:
                self.last_depot_cost = dateindex
                return self.depot_cost
            elif dateindex.month != self.last_depot_cost.month:
                self.last_depot_cost = dateindex
                return self.depot_cost
            elif dateindex.year > self.last_depot_cost.year:
                self.last_depot_cost = dateindex
                return self.depot_cost
            else:
                return self.zero
        elif self.depot_cost_interval == 'yearly':
            if self.last_depot_cost is None:
                self.last_depot_cost = dateindex
                return self.depot_cost
            elif dateindex - self.last_depot_cost >= datetime.timdelta(days=365):
                self.last_depot_cost = dateindex
                return self.depot_cost
            else:
                return self.zero
        else:
            raise RuntimeError
