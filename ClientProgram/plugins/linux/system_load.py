#!/usr/bin/env python
#coding:utf-8
__author__ = 'CQ'

import subprocess


def monitor():
    shell_command = 'uptime'
    status, result = subprocess.getstatusoutput(shell_command)
    if status != 0:  # cmd exec error
        value_dic = {'status': status}
    else:
        uptime = result.split(',')[:1][0]
        # load1,load5,load15 = result.split('load averages:')[1].split(',')
        load1, load5, load15 = result.split('load average:')[1].split()
        value_dic = {
            'uptime': uptime,
            'load1': load1,
            'load5': load5,
            'load15': load15,
            'status': status
        }
    return value_dic


if __name__ == "__main__":
    print(monitor())