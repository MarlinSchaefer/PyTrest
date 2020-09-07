from PyTrest.depot import Portfolio
from PyTrest.depot import DepotHistory
from PyTrest.currency import Money

class BaseDepot(object):
    def __init__(self, name='N/A', base_cash=None, currency='USD',
                 history=None, curr_dateindex=None):
        self.name = str(name)
        self.cash = Money(base_cash, currency=currency)
        if history is None:
            self.history = DepotHistory()
        elif not isinstance(history, DepotHistory):
            raise TypeError
        else:
            self.history = history
        self.curr_dateindex = curr_dateindex
        self.protfolio = Portfolio()
    
    @property
    def currency(self):
        return self.cash.currency
    
    def add_funds(self, funds, dateindex=None):
        assert funds >= 0
        if dateindex is None:
            dateindex = self.curr_dateindex
        self.history.add_funds(funds, dateindex)
        self.cash += funds
    
    def withdraw_funds(self, funds, dateindex=None):
        if dateindex is None:
            dateindex = self.curr_dateindex
        funds = abs(funds)
        self.history.withdraw_funds(funds, dateindex)
        self.cash -= funds
        
    pass
