# Getting Started

## Setup

### Backend

1. Clone the `alphaz` from the repository

```sh
https://github.com/ZAurele/alphaz.git
```

2. Launch the setup

```sh
python setup.py
```

# API

The api is automatically configured from the `api.jon` file.

```python
from alphaz.utils.api import api
```

or

```python
from core import core
api = core.api
```

> `api` is the equivalent for `app` in `Flask` framework.

## Route

### Basic

To specify an api route, juste use the `route` flag:

```python
from alphaz.utils.api import route, api, Parameter

@route("route_name")
def method_name():
    return "hello"
```

Method automatically convert the output to the right format. Default format is `json`

### Description

A description could be specified:

```python
@route("route_name", description="This route say hello")
def method_name():
    return "hello"
```

### Category

The routes are organized by `category`, by default the route category is defined by it **file name**, but it could be specified using the `cat` parameter:

```python
@route("route_name", cat="politeness")
def method_name():
    return "hello"
```

## Parameters

### Simple

You could simply define parameters by listing all parameters in `parameters` list:

```python
from alphaz.utils.api import route, api, Parameter

@route("books", parameters=["name"])
def method_name():
    return "Book name is %s or %s"%(api["name"], api.get("name",default=""))
```

Parameter value is accessed by `api` instance, using `get` method, they could also be accessed using `get_parameters` method from `api` instance.

### Object

Or you could use the `Parameter` class to specify properties such as:

-   **ptype**: value type int, str, bool, `SqlAlchemy model`
    -   parameter is `automatically converted` to the specified type
    -   if conversion failed an `exception` is raised
-   **required**: the parameter is required or not
-   **default**: default parameter value
-   **options**: authorized values
-   **mode**: input mode
-   **cacheable**: parameter is taken into acount in the caching system or not
-   **private**: parameter is hiden from documentation or not

```python
@route("/logs",
    parameters = [
        Parameter('page',required=True,ptype=int),
        Parameter('startDate',required=True),
        Parameter('endDate',default=None),
        Parameter('error', options=["Y","N"])
    ])
def admin_logs():
    return get_logs(**api.get_parameters())
```

> Promote this method as it allows a better control on parameters

### SqlAlchemy model

If you specify a `SqlAlchemy model` as a type it will be automatically converted to the specified model.

```python
from core import core
db = core.db

class Logs(db.Model, AlphaTable):
    __tablename__ = 'LOGS'

    id                       = AlphaColumn(Integer,nullable=False,primary_key=True)
    name                     = AlphaColumn(String,nullable=False)

@route("logs",
    parameters = [
        Parameter('log',ptype=Logs)
    ])
def admin_logs():
    db.add(api['log'])
```

## Methods

Methods are specified the same way as in `Flask`, using `methods` parameter:

```python
@route('logs', methods=["GET"])
def get_logs():
    return db.select(Logs)

@route('logs', methods=["POST"])
def set_logs():
    return db.add(Logs)
```

Methods can be managed using `different routes` or within `a single route`:

```python
@route('logs', methods=["GET", "POST", "DELETE"])
def get_logs():
    if api.is_get():
        return db.select(Logs)
    elif api.is_post():
        return db.add(Logs)
    elif api.is_delete():
        return db.delete(Logs)
```

## Authorizations

> In progress

## Cache

> In progress

## Admin

> In progress
