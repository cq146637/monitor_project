#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'CQ'

import subprocess


def monitor(frist_invoke=1):
    shell_command = 'sar -n DEV 1 5 |grep -v IFACE |grep Average'
    result = subprocess.Popen(shell_command, shell=True, stdout=subprocess.PIPE).stdout.readlines()
    value_dic = {"status": 0, "data": {}}
    for line in result:
        line = line.split()
        nic_name, t_in, t_out = line[1], line[4], line[5]
        value_dic["data"][nic_name.decode()] = {"t_in": t_in.decode(), "t_out": t_out.decode()}
    return value_dic
