from .update import update_yahoo_feed
from ..feed import CandleFeed, YahooFeed
import os
import pandas as pd
import datetime

class WatchList(object):
    def __init__(self, name='NA', tickers=None, storage='.'):
        """An object to keep track of multiple stocks. This is meant to
        give an overview of the daily changes.
        
        Arguments
        ---------
        name : {str, 'NA'}
            The name of the watchlist.
        tickers : {None or list of str, None}
            The ticker-symbols to track (as understood by Yahoo Finance)
        storage : {str, '.'}
            A path to a directory in which the data for these stocks are
            stored.
        """
        self.name = name
        self.tickers = []
        self.feeds = []
        self.storage = storage
        if tickers is not None:
            for ticker in tickers:
                self.add_ticker(ticker)
        #self.tickers = tickers if tickers is not None else []
        #self.feeds = [YahooFeed(ticker) for ticker in self.tickers]
    
    def __len__(self):
        return len(self.feeds)
    
    def __contains__(self, item):
        if isinstance(item, str):
            return item in self.tickers
        elif isinstance(item, CandleFeed):
            return item in self.feeds
        else:
            return False
    
    def add_ticker(self, ticker):
        if ticker in self:
            return
        file_path = os.path.join(self.storage, ticker + '.hdf')
        if os.path.isfile(file_path):
            self.tickers.append(ticker)
            feed = CandleFeed.from_save(file_path)
            update_yahoo_feed(feed)
            feed.set_head_or_prior(datetime.datetime.now())
            self.feeds.append(feed)
            
            return
        feed = YahooFeed(ticker)
        feed.set_head_or_prior(datetime.datetime.now())
        self.tickers.append(ticker)
        self.feeds.append(feed)
        self.update()
    
    def update(self, dateindex=None):
        """Update the data in the stored feeds.
        """
        if dateindex is None:
            dateindex = datetime.datetime.now()
        for feed in self.feeds:
            try:
                update_yahoo_feed(feed, dateindex=dateindex)
            except:
                pass
            feed.set_head_or_prior(dateindex)
    
    @classmethod
    def from_storage(cls, path, name=None, update=True):
        if name is None:
            cont = os.listdir(path)
            #cont = [, pt) for pt in cont]
            print(f'Found contents {cont}')
            files = list(filter(lambda s: os.path.isfile(os.path.join(path, s)), cont))
            print(f'Found files {files}')
            for ffn in files:
                fn, ext = os.path.splitext(ffn)
                print(f'Looking at fn {fn}')
                if fn.startswith('__') and fn.endswith('__'):
                    name = ffn
                    break;
            if name is None:
                raise ValueError('No fitting file found at {}.'.format(path))
        
        if '.' not in name:
            name = name + '.txt'
        
        watchlist_name = os.path.splitext(name)[0][2:-2]
        with open(os.path.join(path, name), 'r') as fp:
            tickers = [line[:-1] for line in fp.readlines()]
        
        feeds = []
        for ticker in tickers:
            load_path = os.path.join(path, ticker + '.hdf')
            feed = CandleFeed.from_save(load_path)
            feeds.append(feed)
        
        ret = WatchList(name=watchlist_name, storage=path)
        ret.tickers = tickers
        ret.feeds = feeds
        
        if update:
            ret.update()
        
        return ret
    
    @classmethod
    def load(cls, filepath, update=True):
        path, name = os.path.split(filepath)
        return cls.from_storage(path, name=name, update=update)
    
    def as_dataframe(self, sorting='tickers'):
        """Converts the table that shoule be printed to a pandas
        dataframe.
        """
        ret_dict = {}
        tickers, feeds = self.sort(sorting=sorting)
        ret_dict['Ticker'] = tickers
        ret_dict['Value'] = [float(feed.value.close) for feed in feeds]
        ret_dict['Diff'] = [self._get_diff(feed) for feed in feeds]
        return pd.DataFrame(ret_dict)
    
    def __str__(self):
        """Apply formatting to the contents.
        """
        return self.get_print_str()
    
    def _get_diff(self, feed):
        curr = feed.value.close
        prev = feed.rloc(-2).close
        return float(curr / prev)
    get_diff = _get_diff
    
    def sort(self, sorting='tickers'):
        """Set the sorting of the contents.
        
        E.g.
        tickers : Sort alphabetically by ticker-names.
        diff : Sort by the difference to the previous close.
        none : Print by insertion order.
        
        Returns
        -------
        tickers : list of str
            The sorted list of str of the tickers.
        feeds : list of CandleFeed
            The sorted list of CandleFeeds.
        """
        if sorting.lower() == 'tickers':
            def func(key):
                return key[0]
        elif sorting.lower() == 'diff':
            def func(key):
                return self._get_diff(key[1])
        elif sorting.lower() == 'none':
            def func(key):
                return 0
        sorted_cont = sorted(list(zip(self.tickers, self.feeds)),
                             key=func)
        tickers = [pt[0] for pt in sorted_cont]
        feeds = [pt[1] for pt in sorted_cont]
        return tickers, feeds
    
    def get_print_str(self, sorting='tickers'):
        tickers, feeds = self.sort(sorting=sorting)
        max_ticker_len = len(max(tickers + ['Tickers'],
                                 key=lambda s: len(s)))
        feed_diffs = [self._get_diff(feed) for feed in feeds]
        feed_diff_str = ['%.2f' % ((diff - 1) * 100) for diff in feed_diffs]
        max_feeds_len = len(max(feed_diff_str + ['Diff'],
                                key=lambda s: len(s)))
        lines = ['Tickers'.ljust(max_ticker_len) + ' | ' + 'Diff',
                 '-' * (max_ticker_len + 2 + max_feeds_len)]
        for ticker, feed in zip(tickers, feed_diff_str):
            app_str = ticker.ljust(max_ticker_len) + ' | ' + feed
            lines.append(app_str)
        lines.append('')
        
        return '\n'.join(lines)
    
    def print(self, sorting='tickers'):
        print(self.get_print_str(sorting=sorting))
    
    def get(self, ticker):
        """Returns the CandleFeed of a ticker symbol.
        """
        if ticker in self.tickers:
            idx = self.tickers.index(ticker)
            return self.feeds[idx]
        else:
            return None
    
    def save(self):
        if not os.path.isdir(self.storage):
            os.makedirs(self.storage)
        with open(os.path.join(self.storage, '__' + self.name + '__.txt'), 'w') as fp:
            for ticker in self.tickers:
                fp.write(ticker)
                fp.write('\n')
        for ticker, feed in zip(self.tickers, self.feeds):
            path = os.path.join(self.storage, ticker + '.hdf')
            feed.save(path)
    
    def to_ticker(self, feed):
        if isinstance(feed, str):
            return feed
        else:
            return feed.name
    
    def remove_ticker(self, ticker):
        if ticker in self:
            ticker = self.to_ticker(ticker)
            self.tickers.remove(ticker)
            for i, feed in enumerate(self.feeds):
                if feed.name == ticker:
                    self.feeds.pop(i)
                    break
