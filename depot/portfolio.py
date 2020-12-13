from ..currency import Money
from .position import Position
from ..types import DateSeries

class PortfolioHistory(DateSeries):
    def position_event(self, position, dateindex, msg=None):
        if msg is None:
            msg = 'Unnamed position movement'
        msg = str(msg)
        if dateindex not in self:
            self.insert_value(dateindex, value=[])
        self.loc(dateindex).append([position, msg])

class Portfolio(object):
    def __init__(self, dateindex=None, history=None):
        self.positions = []
        self.base_positions = {}
        self.history = history if history is not None else PortfolioHistory()
        self.update_dateindex(dateindex)
    
    def update_dateindex(self, dateindex):
        self.dateindex = dateindex
    
    def __contains__(self, item):
        if isinstance(item, Position):
            in_pos = item in self.positions
            in_base = item in self.base_positions.values()
            return in_pos or in_base
        else:
            raise TypeError
    
    def __iter__(self):
        ret = self.positions.copy()
        ret.extend(list(self.base_positions.values()))
        return ret
    
    def add_position(self, position, dateindex=None):
        assert isinstance(position, Position)
        if dateindex is None:
            dateindex = self.dateindex
        self.positions.append(position)
        self.history.position_event(position, dateindex,
                                    msg='Portfolio: Added position')
    
    def remove_position(self, position, dateindex=None):
        if dateindex is None:
            dateindex = self.dateindex
        ret = None
        if position in self.positions:
            ret = self.positions.remove(position)
        elif position in self.base_positions.values():
            ret = self.base_positions.pop(position.candle_feed)
        if ret is not None:
            self.history.position_event(ret, dateindex,
                                        msg='Portfolio: Removed position')
        return ret
    
    def get_base_position(self, candle_feed, currency):
        if candle_feed in self.base_positions:
            return self.base_positions[candle_feed]
        else:
            pos = Position(candle_feed, amount=0,
                           currency=currency)
            self.base_positions[candle_feed] = pos
            return pos
    
    def value(self, currency='USD'):
        val = Money(0., currency=currency)
        for position in self.positions:
            val += position.value(currency=currency)
        for position in self.base_positions.values():
            val += position.value(currency=currency)
        return val
    
    def shares(self):
        ret = {}
        for pos in self.positions:
            if pos.candle_feed not in ret:
                ret[pos.candle_feed] = 0
            if pos.isLong():
                ret[pos.candle_feed] += pos.size
            elif pos.isShort():
                ret[pos.candle_feed] -= pos.size
            else:
                raise RuntimeError
        for cf, pos in self.base_positions.items():
            if cf not in ret:
                ret[cf] = 0
            if pos.isLong():
                ret[cf] += pos.size
            elif pos.isShort():
                ret[cf] -= pos.size
            else:
                raise RuntimeError
        return ret
    
    def reduce_position_size(self, position, amount, dateindex=None,
                             price=None):
        if not position in self:
            msg = 'Cannot sell a position that is not part of this '
            msg += 'Portfolio.'
            raise ValueError(msg)
        cash_delta = position.reduce_position_size(amount,
                                                   dateindex=dateindex,
                                                   price=price)
        if position.size == 0:
            self.remove_position(position)
        return cash_delta, position
    
    def increase_position_size(self, position, amount, dateindex=None,
                               price=None):
        if position not in self:
            raise ValueError
        cash_delta = position.increase_position_size(amount,
                                                     dateindex=dateindex,
                                                     price=price)
        return cash_delta, position
    
    def close_position(self, position, dateindex=None, price=None):
        return self.reduce_position_size(position, position.size,
                                         dateindex=dateindex,
                                         price=price)
    
    def open_position(self, candle_feed, dateindex=None, amount=1,
                         position_type='long', currency='USD',
                         price=None, evaluate_at='low'):
        self.positions.append(Position(candle_feed, dateindex=dateindex,
                                       amount=amount, currency=currency,
                                       open_price=price,
                                       evaluate_at=evaluate_at,
                                       position_type=position_type))
    pass
