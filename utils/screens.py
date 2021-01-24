import subprocess, os, psutil, logging, json, argparse
from logging.handlers import TimedRotatingFileHandler

LOG = None


def error(message):
    global LOG
    print(message)
    LOG.error(message)


def info(message):
    global LOG
    print(message)
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Screens ensure")

    parser.add_argument("--log", "-l")
    parser.add_argument("--file", "-f")

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

    cmd = "screen -ls"
    lines = get_cmd_output(cmd)

    for name, screen in screens.items():
        active = screen["active"]
        if not active:
            continue

        screen_name = screen["name"]
        pid = None
        for line in lines:
            if ".%s " % screen_name in line:
                pid = line.split(".")[0].replace(" ", "")
                pid = int(pid)

        if pid is None:
            os.chdir(screen["dir"])
            cmd = "screen -dm -S %s bash -c '%s; exec bash'" % (
                screen["name"],
                screen["shell_cmd"],
            )
            error("   ==> Restart screen for %s" % name)
            info("Ex: %s" % cmd)
            if active:
                get_cmd_output(cmd)
        else:
            info("Screen %s %s is running ..." % (pid, name))

        p = psutil.Process(pid)
        if len(p.children()) != 0:
            child = p.children()[0]
            child_p = psutil.Process(child.pid)

            running = len(child_p.children()) != 0

            if not running:
                cmd = "screen -S %s -X stuff '%s'$(echo '\015')" % (
                    pid,
                    screen["shell_cmd"],
                )
                if active:
                    get_cmd_output(cmd)
                error(
                    "   ==> Restart process %s %s in screen %s"
                    % (screen["shell_cmd"], pid, name)
                )
            else:
                info(
                    "Process %s %s in screen %s is running ..."
                    % (screen["shell_cmd"], pid, name)
                )

