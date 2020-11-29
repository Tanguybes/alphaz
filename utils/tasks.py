import shlex
import subprocess

def start_celery():
    from core import core

    cmd = 'pkill celery'
    subprocess.call(shlex.split(cmd))

    log_file = core.config.get('celery/log')
    cmd = "celery -A tasks.configuration worker --loglevel=info --logfile="+log_file
    print("   > starting celery worker %s"%cmd)
    #cmd = "celery -A tasks.configuration beat --loglevel=info --logfile="+log_file
    #print("   > starting celery beat %s"%cmd)
    subprocess.Popen(cmd.split(), shell=False)