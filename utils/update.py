from ..feed import YahooFeed, CandleFeed
from ..types.events import Event
import datetime

def update_yahoo_feed(feed, dateindex=None):
    if dateindex is None:
        dateindex = datetime.datetime.now()
    
    start = feed.max_dateindex - datetime.timedelta(days=7)
    end = dateindex
    down_data = YahooFeed(feed.name, start=start, end=end)
    
    for date, candle in zip(down_data.index, down_data.data):
        if date in feed:
            continue
        else:
            feed.add_candle(date, candle)
    return


def update_feed(feed, dateindex=None):
    if dateindex is None:
        dateindex = datetime.datetime.now()
    
    start = feed.max_dateindex - datetime.timedelta(days=7)
    end = dateindex
    down_data = YahooFeed(feed.name, start=start, end=end)
    
    added = 0
    for date, candle in zip(down_data.index, down_data.data):
        if date in feed:
            continue
        else:
            feed.index.append(date)
            feed.data.append(candle)
            added += 1
    if added > 0 and hasattr(feed, 'handler'):
        feed.handler.events += 1
        eventid = feed.handler.events
        event = Event(event_tag='insert_value',
                      emitter=feed,
                      event_id=eventid,
                      args=[feed, feed.index[-1]],
                      kwargs={'value': feed.data[-1]})
        feed.handler.handle_event(event)
