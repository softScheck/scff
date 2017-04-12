#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import configparser
import os
from datetime import datetime
from time import sleep

cfg = configparser.ConfigParser()
fuzzdir = ".scff/fuzzdir"
afl_output = fuzzdir + "/output"

try:
    cfg.read(".scff/scff.cfg")
    afl_input = cfg['FUZZING']['inputdir']
    afl_output = cfg['FUZZING']['outputdir']
    args = cfg['FUZZING']['args']
except:
    print("WARN: Can't load/read .scff/scff.cfg! Assuming fuzzdir = " +  \
        fuzzdir, "and output dir =", afl_output)

try:
    os.unlink("report-cw.txt")
except:
    pass

def getTime():
    return str(datetime.now().strftime('%H:%M:%S'))

def append(findings, crashno, cdir):
    with open("report-cw.txt", "a") as report:
        for finding in findings:
            fc = open(cdir + "/" + finding, 'rb')
            report.write("#%s. %s: %s\n" % (str(crashno), getTime(), str(fc.read())))
            fc.close()
    report.close()

if os.path.isfile(".scff/master"): # distributed mode and we are server
    crashdir = fuzzdir + "/crashes"
else:
    crashdir = afl_output + "/crashes"

if not os.path.exists(crashdir):
    print("WARN:", crashdir, "does not exist!")
    print("HACK: Creating one because the server might have not been started yet.")
    os.makedirs(crashdir)

if os.path.exists(afl_output + "/fuzz0"):
    print("Seems like parallelismn is going on..")
    para = True
else:
    para = False

crashdirs = []

if para:
    for i in range(64): # if you have more than 64 cores, you can change the number ;)
        if os.path.exists(afl_output + "/fuzz" + str(i) + "/crashes"):
            crashdirs.append(afl_output + "/fuzz" + str(i) + "/crashes")
else:
    crashdirs.append(crashdir)

print("Looking for crashes in", crashdirs)
old_findings = []

while True:
    for crashdir in crashdirs:
        findings = []
        print("crashdir dir:", crashdir)
        for finding in os.listdir(crashdir):
            if finding == "README.txt":
                continue
            findings.append(finding)
        crashes = len(findings)
        if crashes > len(old_findings):
            new = list(set(findings) - set(old_findings))
            print(new)
            append(new, crashes, crashdir)
            old_findings = list(findings)
    sleep(15)

