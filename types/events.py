import functools

"""This module provides functionality to call functions based on events.

Usage example:
class MirroredAppendList(object):
    manager = EventManager()
    def __init__(self, parent=None):
        if parent is None:
            self.handler = EventHandler()
        else:
            self.handler = parent.handler
        self.content = []
        self.handler.listen('append', self.append_action)
    
    @manager.send('append')
    def append(self, item):
        self.content.append(item)
    
    def append_action(self, event):
        if event.emitter is not self:
            self.content.append(event.args[1])

Notes
-----
-The EventHandler must be provided in the attribute 'handler' of the
 class.
-The actions that are listened for will only ever receive the Event
 object.
-event.args[1] is appended, because event.args[0] is self.
"""

class Event(object):
    def __init__(self, event_tag, emitter, event_id=0, args=None,
                 kwargs=None):
        self.tag = str(event_tag)
        self.emitter = emitter
        self.id = event_id
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}

class EventHandler(object):
    def __init__(self):
        self.events = 0
        self.subscriptions = {}
    
    def handle_event(self, event):
        event_tag = event.tag
        if event_tag not in self.subscriptions:
            return
        for func in self.subscriptions[event_tag]:
            func(event)
    
    def send(self, event_tag):
        if event_tag not in self.subscriptions:
            self.subscriptions[event_tag] = []
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper_decorator(*args, **kwargs):
                self.events += 1
                event = Event(event_tag=event_tag,
                              emitter=args[0],
                              event_id=self.events,
                              args=args,
                              kwargs=kwargs
                             )
                ret = func(*args, **kwargs)
                self.handle_event(event)
                return ret
            return wrapper_decorator
        return decorator
    
    def listen(self, event_tag, func):
        event_tag = str(event_tag)
        if event_tag not in self.subscriptions:
            self.subscriptions[event_tag] = []
        if func not in self.subscriptions[event_tag]:
            self.subscriptions[event_tag].append(func)
    
    def stop_listen(self, event_tag, func):
        event_tag = str(event_tag)
        if event_tag not in self.subscriptions:
            return False
        if func not in self.subscriptions[event_tag]:
            return False
        return True

class EventMultiHandler():
    def __init__(self, handlers=None):
        if handlers is None:
            self.handlers = []
        else:
            self.handlers = handlers
        self.events = 0
    
    def send(self, event_tag):
        for handler in self.handlers:
            if event_tag not in handler.subscriptions:
                handler.subscriptions[event_tag] = []
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper_decorator(*args, **kwargs):
                self.events += 1
                event = Event(event_tag=event_tag,
                              emitter=args[0],
                              event_id=self.events,
                              args=args,
                              kwargs=kwargs
                             )
                ret = func(*args, **kwargs)
                for handler in self.handlers:
                    handler.handle_event(event)
                return ret
            return wrapper_decorator
        return decorator
    
    def listen(self, event_tag, func):
        for handler in self.handlers:
            handler.listen(event_tag, func)
    
    def stop_listen(self, event_tag, func):
        for handler in self.handlers:
            handler.stop_listen(event_tag, func)

class EventManager(object):
    def send(self, event_tag=None):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(self, *args, **kwargs):
                if event_tag is None:
                    send_tag = str(func.__name__)
                else:
                    send_tag = event_tag
                handler = self.handler.send(send_tag)(func)
                return handler(self, *args, **kwargs)
            return wrapper
        return decorator
