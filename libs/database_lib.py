import datetime 

def convert_value(value):
    if type(value) == str and len(value) > 7 and value[4] == '/' and value[7] == '/':
        return datetime.datetime.strptime(value, '%Y/%m/%d')
    if value == 'now()':
        return datetime.datetime.now()
    return value

def process_entries(models_sources:list,db,table,log,values:list,headers:list=None):
    if headers is not None:
        headers = [x.lower().replace(' ','_') if hasattr(x,'lower') else str(x).split('.')[1] for x in headers]

        entries = [table(**{headers[i]:convert_value(value) for i,value in enumerate(values_list)}) for values_list in values]
    else:
        entries = values

    # db.session.query(class_instance).delete()
    #db.session.add_all(entries)
    for entry in entries:
        db.session.merge(entry)

    db.session.commit()