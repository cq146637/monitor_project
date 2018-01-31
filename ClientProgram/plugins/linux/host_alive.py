# -*- coding: utf-8 -*-
__author__ = 'CQ'
import subprocess


def monitor(frist_invoke=1):
    shell_command = 'uptime'
    result = subprocess.Popen(shell_command, shell=True, stdout=subprocess.PIPE).stdout.read()
    value_dic = {
        'uptime': result,
        'status': 0
    }
    # 只要有主机没有宕机就能将该条命令返回，服务器端只要在指定时间内接收到该条命令返回值，说明主机还存活
    return value_dic


if __name__ == "__main__":
    print(monitor())
