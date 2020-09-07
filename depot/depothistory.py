from PyTrest.types import DateSeries
DepotHistory(object):
    def __init__(self):
        self.cash_history = DateSeries()
        self.position_history = DateSeries()
    
    def add_funds(self, funds, dateindex):
        if dateindex in self.cash_history:
            self.cash_history[dateindex].append(funds)
        else:
            self.cash_history.insert_value(dateindex, value=[funds])
    
    def withdraw_funds(self, funds, dateindex):
        self.add_funds(-funds, dateindex)
    pass
