# Alpha core system 

## Purpose

The **core** is used as a central point to manage various system:
    - [logging system](## Logging)
    - [database access](## Database)
    - [api system](## API)
    - [dynamic configuration](## Configuration)

## How to use

You could:

- Use the **alphaz** core and initiate it at the start of you project:

    ```python
    from alphaz.models.main import AlphaCore

    core = AlphaCore(__file__)
    ```

- Or create a **core.py** file at the **root** of your project containing at least:

    ```python
    from alphaz.models.main import AlphaCore, singleton

    @singleton
    class Core(AlphaCore):

        def __init__(self,file:str):

            super().__init__(file)

    core = Core(__file__)
    ```

!!! note
    This is the recommended way, so that you could custom the Core class

## Logging


```python
from core import core
LOG = core.get_logger('name')
LOG.info('message')
```

### Database

```python
from core import core
DB = core.db
DB_USERS = core.get_database('users')
```


## API

```python
from core import core
API = core.api
```

## Configuration

```python
from core import core
CONFIG = core.config
tmp_directory_path = CONFIG.get('directories/tmp')
```