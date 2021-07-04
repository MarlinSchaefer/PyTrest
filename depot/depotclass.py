from .portfolio import Portfolio
from .depothistory import DepotHistory
from ..currency import Money
from .position import Position
from .taxes import TaxFree
import warnings
import datetime
import pickle

class Depot(object):
    def __init__(self, name='N/A', cash=None, currency=None,
                 portfolio=None, tax=None, dateindex=None):
        self.name = str(name)
        self.history = DepotHistory()
        self.portfolio = portfolio if portfolio is not None else Portfolio()
        self.tax = tax if tax is not None else TaxFree()
        self.update_dateindex(dateindex)
        if cash is None and currency is None:
            msg = 'A currency must be specified.'
            raise ValueError(msg)
        if currency is None:
            if isinstance(cash, Money):
                self.cash = cash
                self.history.cash_event(self.cash, self.dateindex,
                                        msg='Depot: Initialized Depot with cash')
                self.currency = self.cash.currency
            else:
                raise TypeError
        else:
            self.currency = currency
            self.cash = Money(cash, self.currency)
            self.history.cash_event(self.cash, self.dateindex,
                                    msg='Depot: Initialized Depot with cash')
        
        self.base_positions = {}
    
    def __contains__(self, item):
        if isinstance(item, Position):
            return item in self.portfolio
    
    def update_dateindex(self, dateindex):
        all_positions = self.portfolio.positions + list(self.portfolio.base_positions.values())
        self.tax.on_update(dateindex, all_positions)
        if dateindex is None:
            dateindex = datetime.datetime.now()
        self.dateindex = dateindex
        self.portfolio.update_dateindex(dateindex)
    
    def add_cash(self, cash, dateindex=None):
        assert cash > 0
        if dateindex is None:
            dateindex = self.dateindex
        cash = Money(cash, currency=self.currency).convert(self.currency)
        self.cash += cash
        self.history.cash_event(cash, dateindex, msg='Depot: Added cash')
    
    def withdraw_cash(self, cash, dateindex=None):
        assert cash > 0
        if dateindex is None:
            dateindex = self.dateindex
        cash = Money(cash, currency=self.currency).convert(self.currency)
        self.cash -= cash
        self.history.cash_event(cash, dateindex,
                                msg='Depot: Withdrew cash')
    
    def pay_broker(self, cash, dateindex=None, msg=None):
        if dateindex is None:
            dateindex = self.dateindex
        cash = abs(Money(cash, currency=self.currency).convert(self.currency))
        exe = self.cash >= cash
        self.cash -= min(self.cash, cash)
        self.history.cash_event(cash, dateindex, msg=msg)
        return exe
    
    def get_base_position(self, candle_feed):
        return self.portfolio.get_base_position(candle_feed,
                                                currency=self.currency)
    
    def value(self, currency=None):
        if currency is None:
            currency = self.currency
        port_value = self.portfolio.value(currency=currency)
        return self.cash.convert(currency) + port_value
    
    def shares(self):
        return self.portfolio.shares()
    
    def reduce_position_size(self, position, amount, price=None,
                             dateindex=None):
        cash, pos = self.portfolio.reduce_position_size(position,
                                                        amount,
                                                        price=price,
                                                        dateindex=dateindex)
        taxes = self.tax.on_position_reduce(pos)
        cash -= taxes
        self.history.cash_event(taxes, max(pos.history.index),
                                msg='Depot: Taxes on position reduce')
        self.cash = self.cash + cash
        self.history.cash_event(cash, max(pos.history.index),
                                msg='Depot: Cash from position reduce')
    
    def increase_position_size(self, position, amount, price=None,
                               dateindex=None):
        cash, pos = self.portfolio.increase_position_size(position,
                                                          amount,
                                                          price=price,
                                                          dateindex=dateindex)
        taxes = self.tax.on_position_increase(pos)
        cash -= taxes
        self.history.cash_event(taxes, max(pos.history.index),
                                msg='Depot: Taxes on position increase')
        self.cash = self.cash + cash
        self.history.cash_event(cash, max(pos.history.index),
                                msg='Depot: Cash from position increase')
    
    def save(self, filepath):
        with open(filepath, 'wb') as fp:
            pickle.dump(self, fp)
    
    @classmethod
    def load(cls, filepath):
        with open(filepath, 'rb') as fp:
            ret = pickle.load(fp)
        return ret
