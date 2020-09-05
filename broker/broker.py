import PyTrest.depot as dep
import orderhistory as ordhist
import brokercost as bk

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

class BaseBroker(object):
    def __init__(self, depots=None, active_depot=None, history=None, broker_cost=None):
        self.depots = depots
        self.active_depot = active_depot
        #TODO: Replace the order history with a non-base class once implemented.
        self.history = history if history is not None else ordhist.BaseOrderHistory()
        #TODO: Replace broker cost with a non-base class once implemented.
        self.broker_cost = bk.BaseBrokerCost()
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
                raise ValueError(msg)
    
    def get_depot_name(self, depot):
        if isinstance(depot, str):
            return depot
        elif isinstance(depot, dep.BaseDepot):
            for key, val in self.depots.items():
                if val == depot:
                    return key
            return depot.name
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
        name = self.get_depot_name(depot)
        if name is None:
            msg = 'Could not find a depot corresponding to the given '
            msg += 'input.'
            raise KeyError(msg)
        self.active_depot = name
    
    def submit_order(self, order, depot=None):
        """Submit an order to the Broker.
        
        Arguments
        ---------
        order : PyTrest.broker.order
            The order that is placed.
        depot : {str or PyTrest.depot or None, None}
            The depot on which the order is based. (Cash is taken out of
            that depot and positions are added to the depot.) If set to
            None the currently active depot will be used.
        
        Returns
        -------
        filled : bool
            True if the order could be filled, False if it could not be
            filled.
        """
        if depot is not None:
            old_active = self.active_depot
            self.change_active_depot(depot)
        filled = self.process_order(order)
        self.history.add(self, order)
        if depot is not None:
            self.change_active_depot(old_active)
        return filled
    
    def process_order(self, order):
        raise NotImplementedError()
    pass
