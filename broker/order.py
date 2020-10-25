from . import constraints as pytr_const

class BaseOrder(object):
    """
    Arguments
    ---------
    candle_feed : {PyTrest.feed.CandleFeed or None, None}
        The CandleFeed this order targets. Can be None for 'interact'
        type orders.
    constraints : {list of PyTrest.broker.Constraint or None, None}
        A list of Constraints that have to be passed for the order to
        attempt to fill itself.
    order_id : {int or None, None}
        A unique ID that can be used to target this order. Must be a
        positive integer or None.
    command : {str or None, None}
        The command that should be executed by the Broker once all
        Constraints are fulfilled.
    arguments : {dict or None, None}
        The arguments that should be provided to the Broker to perform
        the command. The key give the key-word, whereas the value give
        the actual argument.
    
    Note
    ----
    -A buy order tries to buy shares of the provided CandleFeed. A sell
     order conversely tries to sell shares of the provided CandleFeed. A
     interact order can be used to target other orders to cancel or
     adjust them.
    """
    def __init__(self, candle_feed=None, constraints=None,
                 order_id=None, command=None, arguments=None):
        self.candle_feed = candle_feed
        self.constraints = constraints
        self.order_id = order_id
        self.command = command
        self.arguments = arguments if arguments is not None else {}
    
    @property
    def constraints(self):
        return self._constraints
    
    @constraints.setter
    def constraints(self, constraints):
        if constraints is None:
            self._constraints = []
        else:
            if all([isinstance(constraint, pytr_const.Constraint) for constraint in constraints]):
                self._constraints = list(constraints)
    
    @property
    def command(self):
        return self._command
    
    @command.setter
    def command(self, command):
        if command is None:
            self._command = 'idle'
        elif isinstance(command, str):
            self._command = command.lower()
        else:
            raise TypeError
    
    @property
    def order_id(self):
        return self._order_id
    
    @order_id.setter
    def order_id(self, order_id):
        if order_id is None:
            self._order_id = -1
        elif not isinstance(order_id, int):
            msg = 'The order_id has to be a positive integer. Input was'
            msg += ' of type {}.'
            msg = msg.format(type(order_id))
            raise TypeError(msg)
        elif order_id < 0:
            msg = 'The order_id has to be a positive integer. Input was'
            msg += '{}.'.format(order_id)
            raise ValueError(msg)
        else:
            self._order_id = order_id
    
    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, status):
        translate = {0: 'empty',
                     1: 'inactive',
                     2: 'active',
                     3: 'partially filled',
                     4: 'filled',
                     5: 'failed',
                     6: 'canceled'}
        if not isinstance(status, (int, str)):
            raise TypeError
        if isinstance(status, int):
            if status not in translate:
                raise ValueError
            
            self._status = translate[status]
        else:
            if status.lower() not in list(translate.values()):
                raise ValueError
            
            self._status = status.lower()
    
    @property
    def closed(self):
        closed_status = ['empty', 'partially filled', 'filled',
                         'failed', 'canceled']
        return self.status in closed_status
    
    @property
    def active(self):
        return self.status == 'active'
    
    def add_constraint(self, constraint):
        if not isinstance(constraint, pytr_const.Constraint):
            msg = 'The constraint needs to be of type '
            msg += 'PyTrest.constraints.Constraint. Got type {} '
            msg += 'instead.'
            msg = msg.format(type(constraint))
            raise TypeError(msg)
        self.constraints.append(constraint)
    
    def set_order_id(self, order_id):
        self.order_id = order_id
    
    def parse_dateindex(self, dateindex):
        if dateindex is None:
            if self.candle_feed is None:
                dateindex = datetime.datetime.now()
            else:
                dateindex = self.candle_feed.dateindex
        return dateindex
    
    def evaluate(self, dateindex=None):
        """Returns the command and associated arguments to the Broker.
        
        Arguments
        ---------
        dateindex : {datetime.datetime or None, None}
            The dateindex at which to check the constraints. If set to
            None, the dateindex from the CandleFeed will be used. If no
            CandleFeed is specified the current datetime will be used.
        
        Returns
        -------
        tuple:
            A tuple where the first entry is a string that specifies the
            command for the Broker. All the second entry specifies the
            arguments for the command.
        """
        if self.closed:
            return ('drop_from_queue', {'order_status': self.status})
        dateindex = self.parse_dateindex(dateindex)
        constrains_passed = []
        for constraint in self.constraints:
            const = constraint.check(dateindex)
            constrains_passed.append(const)
        if all(constrains_passed):
            return (self.command, self.arguments)
        else:
            return ('idle', None)

class BuyOrder(BaseOrder):
    def __init__(self, candle_feed, amount, buy_on='high', stop=None,
                 limit=None, order_id=None):
        constraints = []
        #TODO: Stop and Limit orders should probably take "buy_on" into account
        if stop is not None:
            const = pytr_const.StopConstraint(candle_feed=candle_feed,
                                               stop_price=stop,
                                               direction='falling')
            constraints.append(const)
        if limit is not None:
            const = pytr_const.LimitConstraint(candle_feed=candle_feed,
                                                limit_price=limit,
                                                direction='rising')
            constraints.append(const)
        
        arguments = {'amount': amount}
        super().__init__(candle_feed=candle_feed,
                         constraints=constraints,
                         order_id=order_id,
                         command='buy',
                         arguments=arguments
                         )
        self.buy_on = buy_on
        self.status = 'active'
    
    @property
    def buy_on(self):
        return self._buy_on
    
    @buy_on.setter
    def buy_on(self, buy_on):
        if not isinstance(buy_on, str):
            raise TypeError
        buy_on = buy_on.lower()
        if not buy_on in ['high', 'low', 'open', 'close', 'mean']:
            raise ValueError
        self._buy_on = buy_on
    
    def evaluate(self, dateindex=None):
        dateindex = self.parse_dateindex(dateindex)
        candle = self.candle_feed[dateindex]
        price = None
        if self.buy_on == 'high':
            price = candle.high
        elif self.buy_on == 'low':
            price = candle.low
        elif self.buy_on == 'open':
            price = candle.open
        elif self.buy_on == 'close':
            price = candle.close
        elif self.buy_on == 'mean':
            price = (candle.high + candle.low) / 2
        else:
            raise RuntimeError
        self.arguments['price'] = price
        self.arguments['candle_feed'] = self.candle_feed
        return super().evaluate(dateindex=dateindex)
