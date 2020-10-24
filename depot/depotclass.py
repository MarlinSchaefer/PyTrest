from PyTrest.depot.portfolio import Portfolio
from PyTrest.depot.depothistory import DepotHistory
from PyTrest.currency import Money
from PyTrest.depot.position import Position
from PyTrest.depot.taxes import TaxFree
import warnings

class Depot(object):
    def __init__(self, name='N/A', base_cash=None, currency='USD',
                 history=None, curr_dateindex=None, tax=None):
        self.name = str(name)
        self.cash = Money(base_cash, currency=currency)
        if history is None:
            self.history = DepotHistory()
        elif not isinstance(history, DepotHistory):
            raise TypeError
        else:
            self.history = history
        self.curr_dateindex = curr_dateindex
        self.portfolio = Portfolio()
        self.tax = tax if tax is not None else TaxFree(currency=self.currency)
    
    @property
    def currency(self):
        return self.cash.currency
    
    def add_funds(self, funds, dateindex=None):
        assert funds >= 0
        if dateindex is None:
            dateindex = self.curr_dateindex
        self.history.add_funds(funds, dateindex)
        self.cash += funds
    
    def pay_broker(self, cash, dateindex=None, msg=''):
        if dateindex is None:
            dateindex = self.curr_dateindex
        if cash > self.cash:
            msg = 'Insufficient funds to pay the Broker.'
            warnings.warn(msg, RuntimeWarning)
            return False
        else:
            self.cash -= cash
            self.history.pay_broker(cash, dateindex, msg=msg)
            return True
    
    def withdraw_funds(self, funds, dateindex=None):
        if dateindex is None:
            dateindex = self.curr_dateindex
        funds = abs(funds)
        funds = min(self.cash, funds)
        self.history.withdraw_funds(funds, dateindex)
        self.cash -= funds
        return funds
    
    def cash_from_position(self, cash, dateindex=None):
        if dateindex is None:
            dateindex = self.curr_dateindex
        self.history.cash_from_position(cash, dateindex)
        self.cash += cash
        if self.cash < 0.:
            msg = 'After handeling the last Position the cash in the '
            msg += 'Depot {} fell below 0 and is now at {}.'
            msg = msg.format(self.name, str(self.cash))
            warnings.warn(msg, RuntimeWarning)
    
    def add_position(self, position):
        assert isinstance(position, Position)
        self.portfolio.add_position(position)
    
    def open_position(self, candle_feed, dateindex=None, amount=1,
                         position_type='long', currency='USD',
                         price=None, evaluate_at='low'):
        if dateindex is None:
            dateindex = self.curr_dateindex
        pos = Position(candle_feed, dateindex=dateindex, amount=amount,
                       currency=currency, open_price=price,
                       evaluate_at=evaluate_at,
                       position_type=position_type)
        total_cost = pos.open_price * pos.open_amount
        taxes = self.tax.on_position_entry(pos)
        total_cost += taxes
        if total_cost > self.cash:
            msg = 'The depot has insufficient cash assigned. Could not '
            msg += 'open the position.'
            warnings.warn(msg, RuntimeWarning)
        else:
            
            self.cash_from_position(-total_cost, dateindex=dateindex)
            self.portfolio.add_position(pos)
    
    def close_position(self, position, dateindex=None, price=None):
        if dateindex is None:
            dateindex = self.curr_dateindex
        cash_delta = self.portfolio.close_position(position,
                                                   dateindex=dateindex,
                                                   price=price)
        taxes = self.tax.on_position_exit(position)
        cash_delta -= taxes
        self.cash_from_position(cash_delta, dateindex=dateindex)
        self.history.close_position(position, dateindex=dateindex)
    
    def reduce_position_size(self, position, amount, dateindex=None,
                            price=None):
        if dateindex is None:
            dateindex = self.curr_dateindex
        cash_delta = self.portfolio.reduce_position_size(position,
                                                         amount,
                                                         dateindex=dateindex,
                                                         price=price)
        taxes = self.tax.on_position_reduce(position)
        cash_delta -= taxes
        self.cash_from_position(cash_delta, datetime=datetime)
        self.history.reduce_position_size(position, dateindex)
    pass
