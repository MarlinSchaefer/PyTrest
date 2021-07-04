from ..feed import YahooFeed, CandleFeed
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
