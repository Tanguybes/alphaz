# Alpha screens system

**Alpha** integrate a simple utility that enable to ensure that a ``screen`` if running or not. 

- optional arguments:
  * -h, * --help            show this help message and exit
  * --log LOG, -l LOG     log file path
  * --file FILE, -f FILE  Input configuration file
  * --name NAME, -n NAME  Screen name
  * --cmd CMD, -c CMD     Command to run
  * --envs ENVS [ENVS ...], -e ENVS [ENVS ...]
                        Command to run
  * --directory DIRECTORY, -d DIRECTORY
                        Working directory
  * --request REQUEST, -req REQUEST
                        Request to check the response
  * --retries RETRIES, -ret RETRIES
                        Number of check before fail state
  * --sleep SLEEP, -s SLEEP
                        Sleep time (s)
  * --timeout TIMEOUT, -t TIMEOUT
                        Sleep time (s)
  * --message MESSAGE, -m MESSAGE
                        Check message
  * --failed_message FAILED_MESSAGE, -fm FAILED_MESSAGE
                        Failed message
  * --success_message SUCCESS_MESSAGE, -sm SUCCESS_MESSAGE
                        Success message
  * --restart, -r         Force a restart


## Launch

Easy to launch, two modes are available:

1. Configuration file

    ```sh
    python -m alphaz.utils.screens -f <config_file_path>
    ```
    
    The configuration format is the following, it use the [dynamic json alpha configuration syntax](alpha_configuration.md):
    
    ```json
    {
        "screens": {
            "api": {
                "active":    true,
                "name":      "API",
                "dir":       "{{home}}/{{name}}",
                "shell_cmd": "python api.py",
                "request": "http://0.0.0.0:{{port}}/status",
                "fail_message": "Api failed to restart"
            },
            "api": {
                "active":    false,
                "name":      "API",
                "dir":       "{{home}}/{{name}}",
                "shell_cmd": "python api.py",
                "request": "http://0.0.0.0:{{port}}/status",
                "fail_message": "Failed"
            }
        },
        "configurations": {
            "local": {
                "port": "auto"
            },
            "dev": {
                "port": 3000
            },
            "prod": {
                "port": 5000
            }
        },
        "home": "/home/mes",
        "name": "pyMES"
    }
    ```

2. Parameters:

    ```sh
    python -m alphaz.utils.screens * --name TEST * --cmd "python api.py"
    ```

## Help 

```sh
python -m alphaz.utils.screens
```