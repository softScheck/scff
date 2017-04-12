#!/usr/bin/env python3

import configparser
import os
from sys import argv

def die(msg, errorcode=1):
    red = "\033[0;31m"
    diestr = red + "ERROR: " + str(msg) + "\n"
    print(diestr)
    exit(errorcode)

try:
    import boto3
    import botocore # for ratelimit
except ImportError:
    die("Can't import AWS boto, please install python3-boto3")

def dprint(msg):
    if DEBUG:
        print("DEBUG: " + str(msg))


if os.path.exists("/usr/share/scff"):
    DATA_DIR = "/usr/share/scff/"
elif os.path.exists("/usr/local/share/scff"):
    DATA_DIR = "/usr/share/local/share/scff/"
elif os.path.exists(os.path.expanduser("~")+"/.local/share/scff"):
    DATA_DIR = os.path.expanduser("~")+"/.local/share/scff/"
else:
    die("Important scff components missing! Please reinstall!")

DEBUG = "-d" in argv or "--debug" in argv or "--verbose" in argv

SPEEDS = {"slowest" : "t2.nano", "slow" : "t2.micro", "normal" : "m4.large", \
          "fast" : "m4.xlarge", "superfast" : "m4.4xlarge", \
          "extreme" : "m4.10xlarge"}
MACHINES = {"t2.nano" : 0.75, "t2.micro" : 1.5, "t2.medium" : 6, \
            "m4.large" : 14.3, "m4.xlarge" : 28.5, "m4.2xlarge": 57, \
            "m4.4xlarge" : 114, "m4.10xlarge" : 285}
TIME_UNITS = {"h" : 1, "d" : 24, "w" : 24 * 7, "m" : 24 * 30, "y" : 24 * 365}

SORTED_MACHINES = [(k, MACHINES[k]) for k in \
    sorted(MACHINES, key=MACHINES.get, reverse=False)]

SORTED_SPEEDS = [(k, SPEEDS[k]) for k in \
    sorted(SPEEDS, key=SPEEDS.get, reverse=False)]


def get_cfg_handle(cfgfile):
    cfg = ConfigLoader(cfgfile)
    cfg.load()
    cfg.validate()
    dprint(ConfigLoader.cfg_name + "@" + str(ConfigLoader.cfg_handle))
    return ConfigLoader.cfg_handle

class ConfigLoader():
    cfg_handle = None
    cfg_name = None
    def __init__(self, cfgfile):
        ConfigLoader.cfg_name = cfgfile
        ConfigLoader.cfg_handle = configparser.ConfigParser()

    def load(self):
        if os.path.exists(self.cfg_name):
            self.cfg_handle.read(self.cfg_name)
        else:
            die("Project file " + self.cfg_name +  " does not exist.")

    def validate(self):
        try:
            self.cfg_handle['INSTANCES']['gid']
            self.cfg_handle['FUZZING']['target']
            return True
        except:
            die("Invalid config file " + ConfigLoader.cfg_name)

    def get(self, section, key):
        return self.cfg_handle[section][key]


def calcTotalPrice(machine_type, nom, total_hours):
    """ calculate price and return a fancy formatted string """
    cost = search_v(MACHINES, machine_type) * nom * total_hours
    cost = cost/100
    return cost

def mktag(key, val):
    return[{'Key':key, 'Value':val}]

def is_in(dic, searchstr):
    if searchstr in dic:
        return searchstr
    return None

def search_v(dic, searchstr):
    """ search a dictonary and return the value if searchstr is in dict"""
    for k, v in dic.items():
        if k == searchstr:
            return v
    return None

def search_k(dic, searchstr):
    """ search a dictonary and return the key if searchstr is in dict"""
    for k, v in dic.items():
        if v == searchstr:
            return k
    return None

def ec2_and_instance_handles():
    try:
        ec2 = boto3.resource('ec2')
        all_instances = ec2.instances.all()
    except:
        die("Failed to connect to AWS!!\n" \
            + "- Does the file .aws/config exist and has the right region?\n" \
            + "- Does the file .aws/credentials contain the correct keys?")
    try:
        for i in all_instances:
            pass
    except Exception as e:
        die("Failed to retrieve any instances!\n" \
            + str(e) + "\nAre you connected to the internet?")

    return ec2, all_instances

def tag(instance, tagname):
    try:
        for tag in instance.tags:
            if tag.get('Key') == tagname:
                return tag.get('Value')
    except:
        return None
    return None

def get_instances_by_tag(tag_key, tag_value):
    instances = []
    for i in ec2_and_instance_handles()[1]:

        if tag(i, tag_key) == tag_value:
            if i.state.get('Name') != "terminated" \
                and i.state.get('Name') != "shutting-down":
                instances.append(i)
    return instances

def get_instances(state_filter="avail"):
    instance_group = []
    try:
        for i in ec2_and_instance_handles()[1]:
            if state_filter == "avail":
                if i.state.get('Name') != "terminated":
                    instance_group.append(i)
            elif state_filter == "running":
                if i.state.get('Name') == "running":
                    instance_group.append(i)
            elif state_filter == "cmd-accepting":
                if i.state.get('Name') == "running" \
                or i.state.get('Name') == "halted":
                    instance_group.append(i)
            else:
                instance_group.append(i)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "AuthFailure":
            die(e.response["Error"]["Message"] \
             + "\nMake sure that keys in .aws/config are correct"
             + " and clock is synchronized.")
        else:
            die(e.response["Error"]["Message"])
    return instance_group

dprint("sacf lib loaded!")

