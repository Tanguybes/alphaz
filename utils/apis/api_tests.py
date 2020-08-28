import datetime

from ...models.database import main_definitions as defs

def insert():
    db.add(defs.Test(
            name=      'a',
            number=    12,
            text=      'text',
            date=      datetime.datetime.now()
    ))
    return db.select(defs.Test)