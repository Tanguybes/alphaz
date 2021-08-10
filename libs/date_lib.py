import datetime, re

format_date     = "%Y-%m-%d %H:%M:%S"
format_date2    = "%Y/%m/%d %H:%M:%S"
format_date3    = "%d/%m/%Y %H:%M:%S"
format_date_ws  = "%H:%M:%S.%f"
format_date_4   = "%d_%m_%y"

def str_to_datetime_if_needed(date_string):
    if re.findall(r'[0-9]+-[0-9]+-[0-9]+[T\s][0-9]+:[0-9]+:[0-9]+'):
        return str_to_datetime(date_string)
    return date_string

def str_to_datetime(date_string):
    if date_string[2] == '/':
        format_date_selected = format_date3
    elif date_string[4] == '/':
        format_date_selected = format_date2
    elif date_string[2] == ':' and date_string[8] == '.':
        format_date_selected = format_date_ws
    else:
        format_date_selected = format_date

    if len(date_string) == 10:
        format_date_selected = format_date_selected.split()[0]
    output = datetime.datetime.strptime(date_string, format_date_selected)
    return output

def datetime_to_str(o=None,micro=False):
    if o is None:
        o = datetime.datetime.now()
    return str(o.strftime(format_date if not micro else format_date + '.%f'))