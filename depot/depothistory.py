from PyTrest.types import DateSeries

class DepotHistory(object):
    def __init__(self):
        self.cash_history = DateSeries()
        self.position_history = DateSeries()
    
    def add_funds(self, funds, dateindex, msg=None):
        if msg is None:
            msg = 'Added'
        if dateindex in self.cash_history:
            self.cash_history[dateindex].append((str(msg), funds))
        else:
            self.cash_history.insert_value(dateindex, value=[(str(msg), funds)])
    
    def withdraw_funds(self, funds, dateindex, msg=None):
        if msg is None:
            msg = 'Withdrawn'
        self.add_funds(-funds, dateindex, msg=msg)
    
    def pay_broker(self, funds, dateindex, msg=None):
        if msg is None:
            msg = 'Broker'
        self.add_funds(funds, dateindex, msg=msg)
    
    def cash_from_position(self, cash, dateindex, msg=None):
        if msg is None:
            msg = 'From Position'
        self.add_funds(cash, dateindex, msg=msg)
    
    def close_positon(self, position, dateindex):
        if dateindex in self.position_history:
            self.position_history.append(('Closed', position))
        else:
            self.position_history.insert_value(dateindex, value=[('Closed', position)])
    
    def open_position(self, position, dateindex):
        if dateindex in self.position_history:
            self.position_history.append(('Opened', position))
        else:
            self.position_history.insert_value(dateindex, value=[('Opened', position)])
    
    def reduce_position_size(self, position, dateindex):
        if dateindex in self.position_history:
            self.position_history.append(('Reduced', position))
        else:
            self.position_history.insert_value(dateindex, value=[('Reduced', position)])
    pass
