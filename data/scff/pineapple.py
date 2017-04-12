#!/usr/bin/env python3

import configparser
import logging
import os
import shlex
import socket
import subprocess
import threading
from datetime import timedelta
from glob import glob
from sys import argv
from time import sleep

import psutil

print("pineapple.py v1 - the scff daemon")

fpid = os.fork()
if fpid != 0:
    # Running as daemon now. PID is fpid
    exit(0)

class Thread(threading.Thread):
    def __init__(self, shellcmd):
        threading.Thread.__init__(self)
        self.shellcmd = shellcmd

    def run(self):
        logging.info("Start Thread: " + str(self.shellcmd))
        for outp in run_cmd(self.shellcmd):
            echolog(">>" + str(outp))
            print("OP", outp)
        logging.info("Exiting Thread: " + str(self.shellcmd))

logging.basicConfig(
    filename="scff-daemon.log", \
    format='%(asctime)s %(levelname)s: %(message)s', \
    datefmt="%H:%M:%S", \
    level=logging.DEBUG)

logging.getLogger().addHandler(logging.StreamHandler())

logFormatter = logging.Formatter(
    "%(asctime)s [%(levelname)s]  %(message)s", "%H:%M:%S")
rootLogger = logging.getLogger()
"""
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
"""
def list2str(alist):
    astr = ""
    for word in alist:
        astr += word + " "
    return astr

def getRunningFuzzers():
    proc_list = []
    for proc in psutil.process_iter():
        if any(fuzzer in s for s in proc.cmdline()):
            proc_list.append(proc)
        if any("crash-watch" in s for s in proc.cmdline()):
            proc_list.append(proc)
        if any(ROVING_CLIENT in s for s in proc.cmdline()):
            proc_list.append(proc)
        if any(ROVING_SERVER in s for s in proc.cmdline()):
            proc_list.append(proc)
        if any(FUZZDIR + "/target" in s for s in proc.cmdline()):
            proc_list.append(proc)
        if any(targ in s for s in proc.cmdline()):
            if proc not in proc_list:
                proc_list.append(proc)
        # hard coded, in the future someone might use another fuzzer!
        if any("afl-fuzz" in s for s in proc.cmdline()):
            if proc not in proc_list:
                proc_list.append(proc)
    proc_list = set(proc_list) # easy way to filter duplicates ;)
    proc_list = list(proc_list)
    return proc_list

def get_uptime():
    with open('/proc/uptime', 'r') as file:
        uptime = str(timedelta(seconds=float(file.readline().split()[0])))
    return uptime[:-7]

def shcmd(shellcmd):
    Thread(shellcmd).start()

def run_cmd(command_line):
    command_line_args = shlex.split(command_line)

    logging.info('Subprocess: "' + command_line + '"')

    try:
        with subprocess.Popen(
            command_line_args,
            stdout=subprocess.PIPE,
            bufsize = 1,
            universal_newlines=True) as command_line_process:
            for line in command_line_process.stdout:
                echolog(" [" + command_line_args[0] + "] " + str(line))
    except Exception as exception:
        logging.warning("Exception occurred: " + str(exception))
        logging.warning("Subprocess failed")
        return False
    else:
        # no exception was raised
        logging.info("Subprocess " + command_line + " finished")
    return True

def echolog(msg, level="info"):
    if level == "info":
        logging.info(msg)
    elif level == "warn":
        logging.warning(msg)
    elif level == "error":
        logging.error(msg)
    return msg + "\n"

def is_distributed():
    for proc in psutil.process_iter():
        if any(ROVING_SERVER in s for s in proc.cmdline()):
            return "True"
    return "False"

def print_status():
    ret = ""
    if os.path.isfile(".scff/distributed"):
        mode = "Distributed"
    else:
        mode = str(CPU_CORES) + " * " + fuzzer
    ret = ("\nMode: " + mode + " \tUptime: " + get_uptime() + " \tLoad: " \
        + str(os.getloadavg()[0])[:4] + "\tCPU:" \
        + str(int(psutil.cpu_percent(interval=0.2))) \
        + "%")
    if len(getRunningFuzzers()) >= 1:
        ret += ("\nS CMDLINE                                       PID     CPU%   MEM%")
        for proc in getRunningFuzzers():
            if proc.status() == "sleeping":
                status = "zZ"
                status = "S"
            elif proc.status() == "running":
                status = ">>"
                status = "R"
            elif proc.status() == "stopped":
                status = "||"
                status = "T"
            else:
                status = ":("
                status = "D"
            cmdline = list2str(proc.cmdline())
            ret += ( \
                "\n{} {:.42} {}   {}    {}".format( \
                status, \
                cmdline, \
                " " * (45 - min(len(cmdline), 42)) + str(proc.pid), \
                proc.cpu_percent(interval=0.1), \
                str(round(proc.memory_percent(), 2))) \
                )
    else:
        ret += ("\n\t\t*** No running fuzzers found! ***")
    return ret

def start():
    ret = ""
    ret += echolog("Killing remaining fuzzers first (if any)")
    ret += stop()
    if os.path.isfile(".scff/distributed"):
        if os.path.isfile(".scff/master"):
            if os.path.isfile(ROVING_SERVER):
                ret += echolog("Starting Roving server ...")
                shcmd(ROVING_SERVER + " " + FUZZDIR)
                shcmd("./crash-watch.py")
                sleep(3)
                shcmd(ROVING_CLIENT + " 127.0.0.1:8000 " + args)
            else:
                ret += echolog("./roving/server not found!", "error")
        else:
            sleep(4) # wait for the server
            # get master ip from filename - TODO: VERY BAD HACK!
            mip = glob(".scff/172*")[0][6:]
            for i in range(CPU_CORES):
                ret += echolog("Starting client #" +  str(i+1))
                shcmd(ROVING_CLIENT + " " + mip + ":8000 " + args)

    # single mode
    else:
        if CPU_CORES == 1:
            try:
                shcmd("fuzzers/" + fuzzer + " " + str(-1))
                ret += echolog("Started fuzzers/" + fuzzer + " (single core mode)")
            except:
                logging.error("Failed to start " + fuzzer)
        else:
            for i in range(CPU_CORES):
                try:
                    shcmd("fuzzers/" + fuzzer + " " + str(i))
                    ret += echolog("Started fuzzers/" + fuzzer \
                        + " (PAR_ID: " + str(i) + ")")
                except:
                    logging.error("Failed to start " + fuzzer)
        shcmd("./crash-watch.py")
    return ret


def kill():
    ret = ""
    for proc in getRunningFuzzers():
        ret += echolog("killing " + list2str(proc.cmdline()))
        proc.kill()
    return ret

def stop():
    ret = ""
    try:
        for proc in getRunningFuzzers():
            ret += echolog("terminating " + list2str(proc.cmdline()))
            proc.terminate()
    except:
        pass
    sleep(1)
    for proc in getRunningFuzzers():
        ret += echolog("Process "+ list2str(proc.cmdline()) \
            + " is still alive!", "warn")
    return ret

def pause():
    ret = ""
    for proc in getRunningFuzzers():
        ret += echolog("pausing " + list2str(proc.cmdline()))
        proc.suspend()
    return ret

def resume():
    ret = ""
    for proc in getRunningFuzzers():
        ret += echolog("resuming " + list2str(proc.cmdline()))
        proc.resume()
    return ret

def count():
    return str((len(getRunningFuzzers())))

def checkcmd(data, clientsock):
    echolog("recieved: '" + data +"'")
    if data == "status":
        ret = print_status()
    elif data == "start":
        ret = start()
    elif data == "stop":
        ret = stop()
    elif data == "count":
        ret = count()
    elif data == "kill":
        ret = kill()
    elif data == "resume":
        ret = resume()
    elif data == "is-distributed":
        ret = is_distributed()
    elif data == "ping":
        ret = "pong"
    elif data == "quit":
        clientsock.close()
        exit()
    else:
        ret = echolog("INVALID CMD: " + data, "warn")
    ret += "\n"
    clientsock.send(bytes(ret.encode('UTF-8')))


def handler(clientsock, addr):
    while 1:
        data = clientsock.recv(BUFSIZ)
        if not data:
            break
        data = data.decode('UTF-8')
        data = data.replace('\n', '')
        if data not in CMDS:
            clientsock.send(bytes(("not in" + str(CMDS) + "!\n") \
            .encode('UTF-8')))
        else:
            checkcmd(data, clientsock)
    echolog("closing socket")
    clientsock.close()


CMDS = ("start", "pause", "resume", "stop", "report", "status", "kill", \
        "count", "is-distributed", "ping", "quit")

CONFIG_FILE = os.path.expanduser("~") + "/.scff/scff.proj"
ROVING_CLIENT = os.path.expanduser("~") + "/roving/client"
ROVING_SERVER = os.path.expanduser("~") + "/roving/server"
CPU_CORES = psutil.cpu_count()
FUZZDIR = os.path.realpath(os.path.expanduser("~") + "/.scff/fuzzdir")
targ = FUZZDIR + "/target"
fuzzer = ""
args = ""

if not os.path.isfile(CONFIG_FILE):
    echolog(CONFIG_FILE + " NOT found!", "error")
    exit(3)

cfg = configparser.ConfigParser()
cfg.read(CONFIG_FILE)

try:
    args = cfg['FUZZING']['args']
    fuzzer = cfg['FUZZING']['fuzzer']
except:
    echolog("Configfile seems to be corrupt!", "error")
    exit(3)

if __name__ == "__main__":
    HOST = "localhost"
    if len(argv) == 2:
        PORT = int(argv[1])
    else:
        PORT = 5555
    BUFSIZ = 1024
    ADDR = (HOST, PORT)
    serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        serversock.bind(ADDR)
        serversock.listen(2)
    except OSError:
        echolog("Port in use?!")
        exit(1)

    while 1:
        echolog("waiting for connection...")
        clientsock, addr = serversock.accept()
        echolog("...connected from:" + str(addr))
        handler(clientsock, addr)

echolog("Pineapple is shutting down. Goodbye :)")

