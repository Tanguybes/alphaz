import shlex
import subprocess

def start_celery():
    from core import core
    
    cmd = 'pkill celery'
    subprocess.call(shlex.split(cmd))

    log_file = core.config.get('celery/log')
    cmds = [
        "celery","-A","tasks.configuration","worker","--loglevel=info","--logfile="+
        log_file
    ]
    subprocess.Popen(cmds, shell=False)