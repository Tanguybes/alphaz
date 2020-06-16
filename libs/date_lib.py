import datetime

format_date  = "%Y-%m-%d %H:%M:%S"
format_date2 = "%Y/%m/%d %H:%M:%S"

def str_to_datetime(date_string):
    if date_string[4] == '/':
        format_date_selected = format_date2
    else:
        format_date_selected = format_date
    return datetime.datetime.strptime(date_string, format_date_selected)

def datetime_to_str(o):
    return str(o.strftime(format_date))