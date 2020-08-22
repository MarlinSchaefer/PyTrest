from PyTrest.currency import Money

class BaseTax(object):
    def __init__(self):
        return
    
    def on_position_entry(self, position):
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
    
    def on_position_entry(self, position):
        return Money(0., currency='EUR')
    
    def calculate_taxes(self, gains):
        if gains < 0:
            self.tax_free_money += gains
        else:
            self.tax_free_money -= gains
        taxes = abs(self.tax_free_money) * self.tax_rate
        self.tax_free_money *= 0.
        return taxes
    
    def on_position_exit(self, position):
        if position.closed:
            gains = position.returns
        else:
            gains = 0.
        return self.calculate_taxes(gains)
    
    def on_order(self, order):
        return Money(0., currency='EUR')
    
    def on_update(self, date, positions):
        return Money(0., currency='EUR')
    
    def on_dividend(self, dividend):
        return self.calculate_taxes(dividend)
