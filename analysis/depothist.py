import datetime
import numpy as np
import pandas as pd
from ..types import DateSeries
from ..utils import date_range


def cash_evolution(hist):
    cash_evo = DateSeries()
    curr_cash = 0
    for i in range(len(hist)):
        cdate = hist.index[i]
        cdata = hist.data[i]
        for cash, msg in cdata:
            curr_cash += cash
        cash_evo.insert_value(cdate, curr_cash)
    return cash_evo


def tax_evolution(hist):
    tax_evo = DateSeries()
    for i in range(len(hist)):
        curr_cash = 0
        cdate = hist.index[i]
        cdata = hist.data[i]
        for cash, msg in cdata:
            if 'tax' in msg or 'Tax' in msg:
                curr_cash += cash
        tax_evo.insert_value(cdate, curr_cash)
    return tax_evo


def total_tax(hist):
    tax_evo = tax_evolution(hist)
    return sum(tax_evo.data)


def broker_fee_evolution(hist):
    broker_evo = DateSeries()
    for i in range(len(hist)):
        curr_cash = 0
        cdate = hist.index[i]
        cdata = hist.data[i]
        for cash, msg in cdata:
            if msg.startswith('Broker:'):
                curr_cash += cash
        broker_evo.insert_value(cdate, curr_cash)
    return broker_evo


def total_broker_fees(hist):
    broker_evo = broker_fee_evolution(hist)
    return sum(broker_evo.data)


def position_size_evolution(position):
    pos_size_evo = DateSeries()
    hist = position.history
    size = 0
    for i in range(len(hist)):
        date = hist.index[i]
        for event in hist.data[i]:
            size_diff, price = event[0]
            msg = event[1]
            size += size_diff
        pos_size_evo.insert_value(date, value=size)
    return pos_size_evo


def position_value_at(position, date):
    pos_size_evo = position_size_evolution(position)
    idx = max(np.searchsorted(pos_size_evo.index, date, side='right') - 1, 0)
    if idx < len(pos_size_evo.index):
        size = pos_size_evo.data[idx]
    else:
        size = pos_size_evo.data[-1]
    cf = position.candle_feed
    # idx = np.searchsorted(cf.index, date)
    idx = max(np.searchsorted(cf.index, date, side='right') - 1, 0)
    price = cf.data[idx].low
    return size * price


def portfolio_content_evolution(portfolio):
    port_evo = DateSeries()
    hist = portfolio.history
    for i in range(len(hist)):
        date = hist.index[i]
        if len(port_evo) == 0:
            curr_port = []
        else:
            curr_port = port_evo.data[-1].copy()
        for pos, msg in hist.data[i]:
            if msg == 'Portfolio: Removed position' and pos in curr_port:
                curr_port.remove(pos)
            elif msg == 'Portfolio: Added position' and not pos in curr_port:
                curr_port.append(pos)
        port_evo.insert_value(date, value=curr_port)
    return port_evo


def portfolio_value_evolution(portfolio, min_dateindex=None,
                              max_dateindex=None):
    hist = portfolio.history
    if min_dateindex is None:
        min_dateindex = hist.min_dateindex
    if max_dateindex is None:
        max_dateindex = datetime.datetime.now()
    port_evo = portfolio_content_evolution(portfolio)
    port_val_evo = DateSeries()
    if min_dateindex < hist.min_dateindex:
        for date in date_range(min_dateindex, hist.min_dateindex):
            port_val_evo.insert_value(date, 0)
    for date in date_range(hist.min_dateindex, max_dateindex):
        if date < port_evo.min_dateindex:
            val = 0.
        else:
            idx = max(np.searchsorted(port_evo.index,
                                      date,
                                      side='right') - 1,
                      0)
            if idx == len(port_evo.data):
                idx -= 1
            positions = port_evo.data[idx]
            val = 0
            for pos in positions:
                val += position_value_at(pos, date)
        port_val_evo.insert_value(date, value=val)
    return port_val_evo


def depot_value_evolution(depot):
    cash_evo = cash_evolution(depot.history)
    port_val = portfolio_value_evolution(depot.portfolio,
                                         min_dateindex=cash_evo.min_dateindex,
                                         max_dateindex=cash_evo.max_dateindex)
    return cash_evo + port_val


def depothist_to_dataframe(hist, exclude_zero=True):
    dfdata = {'Date': [], 'Amount': [], 'Description': []}
    for i in range(len(hist)):
        cdate = hist.index[i]
        cdata = hist.data[i]
        for cash, msg in cdata:
            if exclude_zero and cash == 0:
                continue
            dfdata['Date'].append(cdate)
            dfdata['Amount'].append(cash)
            dfdata['Description'].append(msg)
        
    return pd.DataFrame(dfdata)
