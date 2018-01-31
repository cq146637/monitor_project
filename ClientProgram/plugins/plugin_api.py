# -*- coding: utf-8 -*-
__author__ = 'CQ'

from plugins.linux import sysinfo, system_load, cpu_mac, memory, network, host_alive, application
import re


def GetLinuxKeepAlive():
    return host_alive.monitor()


def LinuxSysInfo():
    return sysinfo.collect()

def GetLinuxCpuStatus():
    return cpu_mac.monitor()


def GetLinuxMemStatus():
    return memory.monitor()


def GetLinuxNetworkStatus():
    return network.monitor()


def GetAppMySQLStatus():
    """
        由于是监控应用需要把名字过滤出来
    :return:
    """
    name = re.search('GetApp(.*)Status', 'GetAppMySQLStatus').groups()[0]
    return GetApplicationStatus(name)


def GetLinuxLoadStatus():
    return system_load.monitor()


def GetApplicationStatus(name):
    return application.monitor(name)


def WindowsSysInfo():
    from windows import sysinfo as win_sysinfo
    return win_sysinfo.collect()


