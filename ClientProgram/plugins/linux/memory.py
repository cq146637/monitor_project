#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'CQ'

import subprocess


def monitor(frist_invoke=1):
    monitor_dic = {
        'SwapUsage': 'percentage',
        'MemUsage': 'percentage',
    }
    shell_command = "grep 'MemTotal\|MemFree\|Buffers\|^Cached\|SwapTotal\|SwapFree' /proc/meminfo"

    status, result = subprocess.getstatusoutput(shell_command)
    if status != 0:  # 如果status不等于零说明命令执行有误，服务器依据此状态决定数据操作方式
        value_dic = {'status': status}
    else:
        value_dic = {'status': status}
        for i in result.split('kB\n'):
            key = i.split()[0].strip(':')  # 将键名切割出来
            value = i.split()[1]   # 将数值切割出来
            value_dic[key] = value  # 将键值对填入数据字典中

        # 求当前使用的交换空间大小
        value_dic['SwapUsage'] = int(value_dic['SwapTotal']) - int(value_dic['SwapFree'])

        # 求交换空间利用率
        if monitor_dic['SwapUsage'] == 'percentage':
            value_dic['SwapUsage_p'] = str(int(value_dic['SwapUsage']) * 100 /
                                           int(value_dic['SwapTotal']))

        # 求当前使用的内存空间大小
        value_dic['MemUsage'] = int(value_dic['MemTotal']) - (int(value_dic['MemFree']) + int(value_dic['Buffers']) +
                                                 int(value_dic['Cached']))
        if monitor_dic['MemUsage'] == 'percentage':
            value_dic['MemUsage_p'] = str(int(value_dic['MemUsage']) * 100 / int(value_dic['MemTotal']))

    return value_dic


if __name__ == '__main__':
    print(monitor())
