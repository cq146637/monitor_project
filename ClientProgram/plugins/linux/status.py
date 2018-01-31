# -*- coding: utf-8 -*-
__author__ = 'CQ'
import subprocess

def get_network_connect_count(port="3306"):
    """
        获取该应用的网络连接数
    :param shell_cmd:
    :return:
    """
    # shell_cmd = 'netstat -n | grep tcp | grep ' + port + ' | wc -l'
    # shell_res = subprocess.getoutput(shell_cmd)
    data = {"networks": "0", "CLOSED": "0", "LISTEN": "0",
            "SYN_RECV": "0", "SYN_SENT": "0", "ESTABLISHED": "0",
            "ITMED_WAIT": "0", "CLOSING": "0", "TIME_WAIT": "0", "LAST_ACK": "0"}
    # if shell_res:
    #     data["networks"] = shell_res
    # 下面统计链接状态
    shell_cmd = 'netstat -n | grep tcp | grep ' + port
    shell_res_list = subprocess.getoutput(shell_cmd).split('\n')
    count = 0
    if len(shell_res_list) > 1:
        for status in shell_res_list:
            status = status.split()[5]
            if status in data.keys():
                data[status] = str(int(data[status]) + 1)
            else:
                data[status] = "1"
    return data


print(get_network_connect_count())
