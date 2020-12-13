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
