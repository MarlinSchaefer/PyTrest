from ..utils import ProgBar

class BaseBacktester(object):
    def __init__(self, broker, strat):
        self.broker = broker
        self.strat = strat
    
    def start(self, verbose=True):
        start = self.broker.current_dateindex
        count = 0
        while self.broker.current_dateindex != self.broker.max_dateindex:
            count += 1
            self.broker.advance_time()
        self.broker.set_time(start)
        if verbose:
            bar = ProgBar(count, name="Backtesting")
        while self.broker.current_dateindex != self.broker.max_dateindex:
            self.strat.update()
            orders = self.strat.suggest_orders()
            for order in orders:
                self.broker.submit_order(order)
            self.broker.advance_time()
            if verbose:
                bar.iterate()
    
    def reset(self):
        #TODO reset Depot and stuff
        self.broker.set_time(self.broker.min_dateindex)
