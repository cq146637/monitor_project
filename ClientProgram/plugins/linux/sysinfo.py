#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'CQ'

import os
import subprocess
import re


def collect():
    filter_keys = ['Manufacturer', 'Serial Number', 'Product Name', 'UUID', 'Wake-up Type']
    raw_data = {}

    for key in filter_keys:
        try:
            cmd_res = subprocess.getoutput("sudo dmidecode -t system|grep '%s'" % key)
            cmd_res = cmd_res.strip()

            res_to_list = cmd_res.split(':')
            if len(res_to_list) > 1:  # 如果长度大于一说明对应key有值，需要添加到报告数据中
                raw_data[key] = res_to_list[1].strip()
            else:
                raw_data[key] = -1  # -1是对应key没有值，为了保证数据格式，特地填写-1

        except Exception as e:
            print(e)
            raw_data[key] = -2  # -2 是我们自己定义为命令执行出错后值

    # 由于key名不是我们想要的，需要转换一下，这样转换之后有利于服务器端数据处理
    data = {"asset_type": "server"}
    data['manufactory'] = raw_data['Manufacturer']
    data['sn'] = raw_data['Serial Number']
    data['model'] = raw_data['Product Name']
    data['uuid'] = raw_data['UUID']
    data['wake_up_type'] = raw_data['Wake-up Type']

    data.update(cpuinfo())
    data.update(osinfo())
    data.update(raminfo())
    data.update(nicinfo())
    data.update(diskinfo())

    return data


def diskinfo():
    obj = DiskPlugin()
    return obj.linux()


def nicinfo():
    # tmp_f = file('/tmp/bonding_nic').read()
    # raw_data= subprocess.check_output("ifconfig -a",shell=True)
    raw_data = subprocess.getoutput("ifconfig")
    raw_data = raw_data.split("\n")
    nic_header = ["UP", "BROADCAST", "RUNNING", "MULTICAST", "LOOPBACK"]
    nic_dic = {}
    mac_addr = "0"
    raw_ip_addr = "0"
    raw_bcast = "0"
    raw_netmask = "0"
    for line in raw_data:
        try:
            line.strip()
            if len(line) == '':
                continue

            for key in nic_header:
                if key in line:
                    nic_name = line.split(':')[0]

            if nic_name is None:
                continue

            if 'ether' in line:
                mac_addr = line.split('ether')[1].split()[0].strip()

            raw_ip_addr_temp = line.split('inet')
            if len(raw_ip_addr_temp) > 1 and len(raw_ip_addr) == 1:
                raw_ip_addr = raw_ip_addr_temp[1].split('netmask')[0].strip()

            raw_bcast_temp = line.split('broadcast')
            if len(raw_bcast_temp) > 1 and len(raw_bcast) == 1:
                raw_bcast = raw_bcast_temp[1].strip()

            raw_netmask_temp = line.split('netmask')
            if len(raw_netmask_temp) > 1 and len(raw_netmask) == 1:
                raw_netmask = raw_netmask_temp[1].split('broadcast')[0].strip()

            if nic_name not in nic_dic:
                nic_dic[nic_name] = {'name': nic_name,
                                     'macaddress': mac_addr,
                                     'netmask': raw_netmask,
                                     'network': raw_bcast,
                                     'bonding': 0,
                                     'model': 'unknown',
                                     'ipaddress': raw_ip_addr,
                                     }

            else:  # mac already exist , must be boding address
                if nic_name == nic_dic[nic_name]['name']:
                    nic_dic[nic_name] = {'name': nic_name,
                                         'macaddress': mac_addr,
                                         'netmask': raw_netmask,
                                         'network': raw_bcast,
                                         'bonding': 0,
                                         'model': 'unknown',
                                         'ipaddress': raw_ip_addr,
                                         }

            if "RX packets" in line:
                next_ip_line = True
                # 对key初始化
                nic_name = None
                mac_addr = "0"
                raw_ip_addr = "0"
                raw_bcast = "0"
                raw_netmask = "0"

        except Exception:
            continue

    nic_list = []
    for k, v in nic_dic.items():
        nic_list.append(v)

    return {'nic': nic_list}


def raminfo():
    # raw_data = subprocess.check_output(["sudo", "dmidecode" ,"-t", "17"])
    raw_data = subprocess.getoutput("sudo dmidecode -t 17")
    raw_list = raw_data.split("\n")
    raw_ram_list = []
    item_list = []
    for line in raw_list:
        if line.startswith("Memory Device"):
            raw_ram_list.append(item_list)
            item_list = []
        else:
            item_list.append(line.strip())

    ram_list = []
    for item in raw_ram_list:
        item_ram_size = 0
        ram_item_to_dic = {}
        for i in item:
            data = i.split(":")
            if len(data) == 2:
                key, v = data
                if key == 'Size':
                    if v.strip() != "No Module Installed":
                        ram_item_to_dic['capacity'] = v.split()[0].strip() #e.g split "1024 MB"
                        item_ram_size = int(v.split()[0])
                        # print item_ram_size
                    else:
                        ram_item_to_dic['capacity'] = 0

                if key == 'Type':
                    ram_item_to_dic['model'] = v.strip()
                if key == 'Manufacturer':
                    ram_item_to_dic['manufactory'] = v.strip()
                if key == 'Serial Number':
                    ram_item_to_dic['sn'] = v.strip()
                if key == 'Asset Tag':
                    ram_item_to_dic['asset_tag'] = v.strip()
                if key == 'Locator':
                    ram_item_to_dic['slot'] = v.strip()

                # if i.startswith("")
        if item_ram_size == 0:  # empty slot , need to report this
            pass
        else:
            ram_list.append(ram_item_to_dic)

    # get total size(mb) of ram as well
    # raw_total_size = subprocess.check_output(" cat /proc/meminfo|grep MemTotal ",shell=True).split(":")
    raw_total_size = subprocess.getoutput("cat /proc/meminfo|grep MemTotal ").split(":")
    ram_data = {'ram': ram_list}
    if len(raw_total_size) == 2:  # correct
        total_mb_size = int(raw_total_size[1].split()[0]) / 1024
        ram_data['ram_size'] = total_mb_size

    return ram_data


def osinfo():
    # distributor = subprocess.check_output(" lsb_release -a|grep 'Distributor ID'",shell=True).split(":")
    distributor = subprocess.getoutput("lsb_release -a|grep 'Distributor ID'").split(":")
    # release  = subprocess.check_output(" lsb_release -a|grep Description",shell=True).split(":")
    release = subprocess.getoutput("lsb_release -a|grep Description").split(":")
    data_dic = {
        "os_distribution": distributor[1].strip() if len(distributor) > 1 else None,
        "os_release": release[1].strip() if len(release) > 1 else None,
        "os_type": "linux",
    }
    return data_dic


def cpuinfo():
    base_cmd = 'cat /proc/cpuinfo'
    raw_data = {
        'cpu_model': "%s |grep 'model name' |head -1 " % base_cmd,
        'cpu_count':  "%s |grep  'processor'|wc -l " % base_cmd,
        'cpu_core_count': "%s |grep 'cpu cores' |awk -F: '{SUM +=$2} END {print SUM}'" % base_cmd,
    }

    for k, cmd in raw_data.items():
        try:
            # cmd_res = subprocess.check_output(cmd,shell=True)
            cmd_res = subprocess.getoutput(cmd)
            raw_data[k] = cmd_res.strip()

        # except Exception,e:
        except ValueError as e:
            print(e)

    data = {
        "cpu_count": raw_data["cpu_count"],
        "cpu_core_count": raw_data["cpu_core_count"]
        }
    cpu_model = raw_data["cpu_model"].split(":")
    if len(cpu_model) > 1:
        data["cpu_model"] = cpu_model[1].strip()
    else:
        data["cpu_model"] = -1

    return data


class DiskPlugin(object):

    # def linux(self):
    #     result = {'physical_disk_driver': []}
    #
    #     try:
    #         script_path = os.path.dirname(os.path.abspath(__file__))
    #         shell_command = "sudo %s/MegaCli  -PDList -aALL" % script_path
    #         output = subprocess.getstatusoutput(shell_command)
    #         result['physical_disk_driver'] = self.parse(output[1])
    #     except Exception as e:
    #         result['error'] = e
    #     return result

    def linux(self):
        raw_data = subprocess.getoutput("fdisk -l")
        raw_data = raw_data.split("\n")
        disk_list = {}
        disk = ""
        add_list = []
        index = 0
        for line in raw_data:
            if line == "":
                continue
            if index == 0:
                try:
                    disk = line.split('Disk ')[1].split(': ')[0].strip()
                    total = line.split('Disk ')[1].split(': ')[1].split(',')[1].split()[0]
                    index += 1
                    if len(disk) == 8:
                        disk_list[disk] = {'total': total, 'idle': '', 'usage': '', 'usage_p': ''}
                        continue
                except Exception:
                    pass
            if re.search(disk, line) is None:
                continue
            try:
                if index == 1:
                    temp = line.split("*")[1].split()[0]
                    add_list.append(temp)
                    index += 1
                elif index == 2:
                    temp = line.split()[2]
                    add_list.append(temp)
            except Exception:
                pass
        disk_list[disk]["usage"] = str(int(add_list[1]) - int(add_list[0]))  # B
        disk_list[disk]['idel'] = str(int(disk_list[disk]["total"]) - int(disk_list[disk]["usage"]))
        disk_list[disk]['usage_p'] = str(round(int(disk_list[disk]["usage"]) * 100 / int(disk_list[disk]["total"]), 2))
        disk_list[disk]['name'] = disk
        return {'disk': disk_list[disk]}

    def parse(self, content):
        """
        解析shell命令返回结果
        :param content: shell 命令结果
        :return:解析后的结果
        """
        response = []
        result = []
        for row_line in content.split("\n\n\n\n"):
            result.append(row_line)
        for item in result:
            temp_dict = {}
            for row in item.split('\n'):
                if not row.strip():
                    continue
                if len(row.split(':')) != 2:
                    continue
                key, value = row.split(':')
                name = self.mega_patter_match(key)
                if name:
                    if key == 'Raw Size':
                        raw_size = re.search('(\d+\.\d+)', value.strip())
                        if raw_size:

                            temp_dict[name] = raw_size.group()
                        else:
                            raw_size = '0'
                    else:
                        temp_dict[name] = value.strip()

            if temp_dict:
                response.append(temp_dict)
        return response

    def mega_patter_match(self, needle):
        grep_pattern = {'Slot': 'slot', 'Raw Size': 'capacity', 'Inquiry': 'model', 'PD Type': 'iface_type'}
        for key, value in grep_pattern.items():
            if needle.startswith(key):
                return value
        return False


if __name__ == "__main__":
    print(DiskPlugin().linux())
