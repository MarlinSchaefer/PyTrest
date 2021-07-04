import datetime as dt

def format_datetime(datetime):
    if datetime is None:
        datetime = dt.datetime.now()
    elif isinstance(datetime, dt.date):
        d = datetime
        datetime = dt.datetime(year=d.year,
                                month=d.month,
                                day=d.day
                                )
    return datetime

def date_range(start, end, step=None):
    if step is None:
        step = dt.timedelta(days=1)
    ret = [start]
    while ret[-1] + step < end:
        ret.append(ret[-1] + step)
    return ret
