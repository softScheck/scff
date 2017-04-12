#!/bin/sh

sudo sh -c 'echo core > /proc/sys/kernel/core_pattern'

./start-server
