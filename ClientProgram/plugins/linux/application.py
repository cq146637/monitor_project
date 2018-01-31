# -*- coding: utf-8 -*-
__author__ = 'CQ'

import subprocess


def collect(pid):
    """
        收集主机上该应用的CPU、内存、运行时间、
    :param shell_cmd:
    :return:
    """
    shell_cmd = 'top -n 1 -p ' + pid
    shell_res = subprocess.getoutput(shell_cmd)
    data = {'cpu_p': '0', 'mem_p': '0', 'mem': '0'}
    if shell_res:
        list1 = shell_res.split('\n')[-3].split()[-8:-2]
        data['time'] = list1[5]
        data['cpu_p'] = list1[3]
        data['mem_p'] = list1[4]
        data['mem'] = list1[0]
    return data


def get_threads_count(app_name):
    """
        获取当前应用的线程数
    :param shell_cmd:
    :return:
    """
    shell_cmd = 'ps -eLf | grep -i ' + app_name + ' | wc -l'
    shell_res = subprocess.getoutput(shell_cmd)
    data = {"threads": "0"}
    if shell_res:
        count = str(int(shell_res) - 2)  # 当前命令一个线程，grep 一个线程
        data["threads"] = count
    return data


def get_network_connect_count(port):
    """
        获取该应用的网络连接数
    :param shell_cmd:
    :return:
    """
    shell_cmd = 'netstat -n | grep tcp | grep ' + port + ' | wc -l'
    shell_res = subprocess.getoutput(shell_cmd)
    data = {"networks": "0", "CLOSED": "0", "LISTEN": "0",
            "SYN_RECV": "0", "SYN_SENT": "0", "ESTABLISHED": "0",
            "ITMED_WAIT": "0", "CLOSING": "0", "TIME_WAIT": "0", "LAST_ACK": "0"}
    if shell_res:
        data["networks"] = shell_res

    # 下面统计链接状态
    shell_cmd = 'netstat -n | grep tcp | grep ' + port
    shell_res_list = subprocess.getoutput(shell_cmd).split('\n')
    if len(shell_res_list) > 1:
        for status in shell_res_list:
            status = status.split()[5]
            if status in data.keys():
                data[status] = str(int(data[status]) + 1)
            else:
                data[status] = "1"
    return data


def get_application_port(app_name):
    """
        获取该应用使用的端口
    :param app_name:
    :return:
    """
    shell_cmd = "netstat -ntlp | grep -i " + app_name
    shell_res = subprocess.getoutput(shell_cmd)
    port = None
    if shell_res:
        port = shell_res.split()[3].split(':')[1]
    return port


def get_application_pid(app_name):
    """
        获取该应用运行的进程ID
    :param app_name:
    :return: pid
    """
    shell_cmd = 'ps -aux | grep -i ' + app_name
    shell_res = subprocess.getoutput(shell_cmd).split('\n')
    if len(shell_res) < 2:
        shell_res = None
    else:
        shell_res = shell_res[0]
    pid = None
    if shell_res:
        pid = shell_res.split()[1]
    return pid


def monitor(app_name):
    data = {"status": 0}
    pid = get_application_pid(app_name)

    if pid:

        data.update(collect(pid))

        data.update(get_threads_count(app_name))

        port = get_application_port(app_name)
        if port:

            data.update(get_network_connect_count(port))

    else:
        data.update({'cpu_p': '0', 'mem_p': '0', 'mem': '0', 'time': '0','threads': '0', 'networks': '0'})

    return data


if __name__ == '__main__':
    # put_application_name()
    # name = get_application_list()[0]
    # pid = get_application_pid(name)
    # shell_cmd = 'top -n 1 -p ' + pid
    # data = collect(shell_cmd)
    # print(data)
    # shell_cmd = 'ps -eLf | grep -i zhuozhi | wc -l'
    # data = get_threads_count(shell_cmd)
    # print(data)
    # port = get_application_port('mysql')
    # print(port)
    # shell_cmd = 'netstat -n | grep tcp | grep ' + port + ' | wc -l'
    # data = get_network_connect_count(shell_cmd)
    # print(data)
    monitor("MySQL")





