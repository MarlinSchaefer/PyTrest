from PyTrest.currency import Money

class BaseTax(object):
    def __init__(self):
        return
    
    def on_position_entry(self, position):
        raise NotImplementedError('Function needs to be implemented.')
    
    def on_position_reduce(self, position):
        raise NotImplementedError('Function needs to be implemented.')
    
    def on_position_increase(self, position):
        raise NotImplementedError('Function needs to be implemented.')
    
    def on_position_exit(self, position):
        raise NotImplementedError('Function needs to be implemented.')
    
    def on_order(self, order):
        raise NotImplementedError('Function needs to be implemented.')
    
    def on_update(self, date, positions):
        raise NotImplementedError('Function needs to be implemented.')
    
    def on_dividend(self, dividend):
        raise NotImplementedError('Function needs to be implemented.')

class TaxFree(BaseTax):
    def __init__(self, currency='USD'):
        self.zero = Money(0., currency=currency)
    
    def on_position_entry(self, position):
        return self.zero
    
    def on_position_reduce(self, position):
        return self.zero
    
    def on_position_increase(self, position):
        return self.zero
    
    def on_position_exit(self, position):
        return self.zero
    
    def on_order(self, order):
        return self.zero
    
    def on_update(self, date, positions):
        return self.zero
    
    def on_dividend(self, dividend):
        return self.zero

class GermanTax(BaseTax):
    def __init__(self, tax_rate=0.25):
        self.tax_rate = tax_rate
        self.tax_free_money = Money(0., currency='EUR')
        self.zero = Money(0., currency='EUR')
    
    def on_position_entry(self, position):
        return self.zero
    
    def calculate_taxes(self, gains):
        self.tax_free_money -= gains
        if self.tax_free_money < 0:
            taxes = -self.tax_free_money * self.tax_rate
            self.tax_free_money *= 0.
        else:
            taxes = self.zero
        return taxes
    
    def on_position_reduce(self, position):
        hist = position.history
        dateindex = max(hist.keys())
        amount = hist[dateindex][-1][0]
        curr_price = hist[dateindex][-1][1]
        curr_val = amount * curr_price
        init_val = amount * position.open_price
        if position.position_type == 'long':
            returns = curr_val - init_val
        else:
            returns = init_val - curr_val
        return self.calculate_taxes(returns)
    
    def on_position_increase(self, position):
        return self.zero
    
    def on_position_exit(self, position):
        return self.on_position_reduce(position)
    
    def on_order(self, order):
        return self.zero
    
    def on_update(self, date, positions):
        return self.zero
    
    def on_dividend(self, dividend):
        return self.calculate_taxes(dividend)
