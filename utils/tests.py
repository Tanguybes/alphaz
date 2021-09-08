import subprocess, os, psutil, logging, json, argparse, time, re

from logging.handlers import TimedRotatingFileHandler

from ..libs import test_lib

from core import core

LOG = None

def error(message,quit=False):
    if message is None or message.strip() == "":
        if quit:
            exit()
        return
    global LOG
    print("ERROR: %s"%message)
    if LOG is not None:
        LOG.error(message)
    if quit:
        exit()

def info(message, end="\n"):
    if message is None or message.strip() == "":
        return
    global LOG
    print("INFO: %s"%message,end=end)
    if LOG is not None:
        LOG.info(message)

def log_config():
    global LOG
    
    LOG = logging.getLogger(log_file.split(os.sep)[-1].split(".")[0])
    LOG.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_handler = TimedRotatingFileHandler(log_file, when="midnight", backupCount=30)
    log_handler.setFormatter(formatter)
    LOG.addHandler(log_handler)
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ensure that a screen is running")

    parser.add_argument("--categories", "-CAT", nargs="+", default=[], help="Test categories")
    parser.add_argument("--groups", "-G", nargs="+", default=[], help="Test groups")
    parser.add_argument("--names", "-N", nargs="+", default=[], help="Test names")

    parser.add_argument("--run", "-r", type=bool, help="Run the test or not")
    
    parser.add_argument("--configuration", "-c", help="Configuration to run")
    parser.add_argument("--log", "-l", help="Log file")
    parser.add_argument("--directory", "-d", help="Working directory")

    args = parser.parse_args()

    log_file = args.log

    core.set_configuration(args.configuration)

    
    test_modules = core.config.get('directories/tests') if args.directory is None else args.directory

    test_categories = test_lib.get_tests_auto(test_modules)

    


    exit()


