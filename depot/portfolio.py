from PyTrest.depot import Position

class Portfolio(object):
    def __init__(self):
        self.positions = []
    
    def add_position(self, candle_feed, dateindex=None, amount=1,
                     position_type='long', currency='USD', price=None,
                     evaluate_at='low', ):
        self.positions.add(Position(candle_feed, dateindex=dateindex,
                                    amount=amount, currency=currency,
                                    open_price=price,
                                    evaluate_at=evaluate_at,
                                    position_type=position_type))
    
    def value(self, currency='USD'):
        val = Money(0., currency=currency)
        for position in self.positions:
            val += position.value()
        return val
    
    def sell_position_parts(self, position, amount, dateindex=None,
                            price=None):
        if not position in self.positions:
            msg = 'Cannot sell a position that is not part of this '
            msg += 'Portfolio.'
            raise RuntimeError(msg)
        sell_price = position.reduce_position_size(amount,
                                                   dateindex=dateindex,
                                                   price=price)
        if position.size == 0:
            self.positions.remove(position)
            return sell_price, position
        else:
            return sell_price
    
    def sell_position(self, position, dateindex=None, price=None):
        return self.sell_position_parts(position, position.size,
                                        dateindex=dateindex,
                                        price=price)
    pass
