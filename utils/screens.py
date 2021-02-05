import subprocess, os, psutil, logging, json, argparse, time, re
from logging.handlers import TimedRotatingFileHandler
from screenutils import list_screens, Screen
import requests

LOG = None


def error(message):
    global LOG
    print(message)
    LOG.error(message)


def info(message, end="\n"):
    global LOG
    print(message,end=end)
    LOG.info(message)


def get_cmd_output(cmd):
    result = subprocess.check_output(cmd, shell=True)
    lines = str(result).split("\\n")
    i = 0
    output_lines = []
    for line in lines:
        line = line.replace("\\t", "    ").replace("\\r", "")
        output_lines.append(line)
        i += 1
    return output_lines

def replace_envs(text):
    if type(text) != str:
       return text
    envs = re.findall(r"\$[_a-zA-Z]+",text)
    for env in envs:
        if env[1:] in os.environ:
            text = text.replace(env, os.environ[env[1:]].strip())
    return text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Screens ensure")

    parser.add_argument("--log", "-l")
    parser.add_argument("--file", "-f")
    parser.add_argument("--restart", "-r",action="store_true")

    args = parser.parse_args()

    log_file = args.log if args.log is not None else "screens.log"

    LOG = logging.getLogger(log_file.split(os.sep)[-1].split(".")[0])
    LOG.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_handler = TimedRotatingFileHandler(log_file, when="midnight", backupCount=30)
    log_handler.setFormatter(formatter)
    LOG.addHandler(log_handler)

    if not args.file:
        exit()

    file_path = args.file
    if not ".json" in file_path:
        file_path = file_path + ".json"
    if not os.path.exists(file_path):
        exit()
    screens = {}
    with open(file_path, "r") as f:
        screens = json.load(f)

    screens_list = list_screens()
        
    for name, screen in screens.items():
        screen = {x:replace_envs(y) for x,y in screen.items()}
        active = screen["active"]
        if not active:
            continue

        screen_name = screen["name"]
        
        screen_exist_list = [x for x in screens_list if x.name == screen_name]
        if len(screen_exist_list) != 0:
            for screen_entity in screen_exist_list:
                info("Screen %s %s is running ..." % (screen_entity.id, screen_entity.name))
                if args.restart:
                    screen_entity.kill()
                    info("   screen %s %s killed ..." % (screen_entity.id, screen_entity.name))
        
        if len(screen_exist_list) == 0 or args.restart:
            s = Screen(screen_name,True)
            s.send_commands("cd %s"%screen["dir"])
            s.send_commands(screen["shell_cmd"])
            s.detach()
            
            info("   ==> Screen %s restarted" % screen_name)
            
            restarted = False
            if "request" in screen:
                info("   ==> Api restarting ...")
                info("      Fetching %s"%screen["request"])
                time.sleep(5)
                
                times = 10
                for i in range(times):
                    if restarted:
                        continue
                    try:
                        print('         ' + '.'*(times - i))
                        r = requests.get(screen["request"], timeout=10)
                        if "success" in str(r.content):
                            info("   ==> Api restarted")
                            restarted = True
                            continue
                    except Exception as ex:
                        time.sleep(5)
                if not restarted:
                    error("   ==> Api not restarted !")
                    error("   ==> Appeler l'astreinte MES ...")

