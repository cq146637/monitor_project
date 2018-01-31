# -*- coding: utf-8 -*-
__author__ = 'CQ'

import json
import time
import re
import pickle
import requests
import threading
from conf import settings
from plugins import plugin_api


class ClientHandle(object):

    def __init__(self):
        self.monitored_services = {}   # 监控服务列表
        self.get_host_id()   # 获取当前主机的ID号，并保存到settings文件中
        self.send_sysinfo()   # 发送当前主机的系统信息到服务器，有且只发送一次

    def get_host_id(self):
        """向服务器获取本机id"""
        pass

    def save_application_name(self):
        """
        保存要监控应用的名称,现在没有用了，改变了策略，直接传入应用名称
        :return:
        """
        file = open('../plugins/linux/application_name.txt', 'wb')
        name_list = []
        try:
            for s_name in self.monitored_services['services'].keys():
                if re.search('Linux', s_name, re.I) is None and re.search('Windows', s_name, re.I) is None:
                    name_list.append(s_name)
            pickle_list = pickle.dumps(name_list)
            file.write(pickle_list)
            file.close()
        except Exception:
            file.truncate()  # 如果出错清空文件内容
            pickle_list = pickle.dumps([])
            file.write(pickle_list)
            file.close()

    def send_sysinfo(self):
        """
            客户端代理一开启就立马向服务发送一份系统汇总信息
        :return:
        """
        func = getattr(plugin_api, "LinuxSysInfo")
        plugin_callback = func()
        report_data = {
            'client_id': settings.configs['HostID'],  # 顺便告诉服务器这是哪台主机，服务器依据此做redis_KEYS匹配
            'data': json.dumps(plugin_callback)  # 将监控服务的具体数据序列化，准备发送给服务器
        }
        # 获取发送报告的URL，和HTTP方法
        request_action = settings.configs['urls']['send_host_sysinfo'][1]
        request_url = settings.configs['urls']['send_host_sysinfo'][0]
        print(request_action, request_url)
        # report_data = json.dumps(report_data)
        print('---sysinfo data:', report_data)  # 顺便打印一下报告数据
        self.url_request(request_action, request_url, params=report_data)

    def load_latest_configs(self):
        """
        load the latest monitor configs from monitor server
        下载最新的监控任务（每5分钟获取一次）
        :return:
        """
        request_type = settings.configs['urls']['get_configs'][1]  # 获取urls
        url = "%s/%s" % (settings.configs['urls']['get_configs'][0], settings.configs['HostID'])  # 获取主机ID
        latest_configs = self.url_request(request_type, url)  # 发送HTTP请求，并获取返回信息
        latest_configs = json.loads(latest_configs)  # 将接收到的json数据转换成原来的数据格式（字典）
        self.monitored_services.update(latest_configs)   # 利用字典的update方法将互异的键值对更新

    def forever_run(self):
        """
        start the client program forever
        :return:
        """
        exit_flag = False  # 只要退出代码不为True就一直循环发送监控报告
        config_last_update_time = 0  # 初始化给0是为了在刚开始就向服务器获取一次监控任务，不用等定时周期到来
        while not exit_flag:
            if time.time() - config_last_update_time > settings.configs['ConfigUpdateInterval']:
                self.load_latest_configs()  # 获取监控任务
                print("Loaded latest config:", self.monitored_services)  # 输出显示获取到的监控服务有哪些
                config_last_update_time = time.time()   # 把当前时间戳记录，等待5分钟后再次获取监控任务

            for service_name, val in self.monitored_services['services'].items():
                #  在原有的字典中加入时间戳，利用时间戳对比监控周期，既利用原有的字典，又达成周期计时
                # self.monitored_services数据格式{'services':{'"LinuxMemory":['GetLinuxMemStatus', 90, 16484946]'}}
                # service_name = 'LinuxMemory'
                # val = ['GetLinuxMemStatus', 90, 16484946]
                if len(val) == 2:
                    # 这里第一次将添加时间戳为0是为了立刻发送监控数据给服务器端
                    self.monitored_services['services'][service_name].append(0)
                monitor_interval = val[1]
                last_invoke_time = val[2]
                if time.time() - last_invoke_time > monitor_interval:
                    # 如果大于监控报告定时了，说明要发送监控数据了，就需要执行我们定义好的插件，并将数据发送报告给服务器
                    # print(last_invoke_time, time.time())
                    # 执行插件前将时间戳更新，以便下一次判断
                    self.monitored_services['services'][service_name][2] = time.time()
                    # 为了不影响主线程，因为主线程为多个服务提供计时服务，不能在主线程执行插件、发送报告，所以用多线程
                    t = threading.Thread(target=self.invoke_plugin, args=(service_name, val))
                    t.start()
                    print("监控 [%s] 报告已经发送完毕！！！" % service_name)
                else:
                    print("Going to monitor [%s] in [%s] secs" % (service_name,
                                                                  monitor_interval - (time.time()-last_invoke_time)))
            time.sleep(1)  # 每一秒种循环检测所有的服务

    def invoke_plugin(self, service_name, val):
        """
        invoke the monitor plugin here, and send the data to monitor server after plugin returned status data each time
        执行监控插件并发送报告给服务器端
        :param val: [pulgin_name,monitor_interval,last_run_time]
        :return:
        """
        plugin_name = val[0]
        # 利用反射获取插件名，plugin包中定义好了对应的函数，只要插件名函数名同一即可执行
        if hasattr(plugin_api, plugin_name):
            func = getattr(plugin_api, plugin_name)
            plugin_callback = func()  # 这里已经获取了当前主机监控服务的具体数据

            report_data = {
                'client_id': settings.configs['HostID'],  # 顺便告诉服务器这是哪台主机，服务器依据此做redis_KEYS匹配
                'service_name': service_name,   # 顺便告诉服务器这是什么服务的监控数据，服务器依据此来对数据进行分类
                'data': json.dumps(plugin_callback)  # 将监控服务的具体数据序列化，准备发送给服务器
            }

            # 获取发送报告的URL，和HTTP方法
            request_action = settings.configs['urls']['service_report'][1]
            request_url = settings.configs['urls']['service_report'][0]

            # report_data = json.dumps(report_data)
            print('---report data:', report_data)   # 顺便打印一下报告数据
            self.url_request(request_action, request_url, params=report_data)
        else:
            print("\033[31;1mCannot find service [%s]'s plugin name [%s] in plugin_api\033[0m" %
                  (service_name, plugin_name))
        print('--plugin:', val)

    def url_request(self, action, url, **extra_data):
        """
        cope with monitor server by url
        HTTP请求
        :param action: "get" or "post"
        :param url: witch url you want to request from the monitor server
        :param extra_data: extra parameters needed to be submited
        :return:
        """
        abs_url = "http://%s:%s/%s" % (settings.configs['Server'],
                                       settings.configs["ServerPort"],
                                       url)
        if action in ('get', 'GET'):
            try:
                res = requests.get(abs_url, timeout=settings.configs['RequestTimeout'])
                res.encoding = 'utf-8'
                callback = res.text
                return callback
            except requests.exceptions.RequestException as e:
                exit("\033[31;1m%s\033[0m" % e)

        elif action in ('post', 'POST'):
            try:
                payload = extra_data['params']
                headers = {'Content-Type': "application/x-www-form-urlencoded"}
                res = requests.post(url=abs_url, headers=headers, data=payload,
                                    timeout=settings.configs['RequestTimeout'])
                res.encoding = 'utf-8'
                callback = res.text
                callback = json.loads(callback)
                print("\033[31;1m[%s]:[%s]\033[0m response:\n%s" % (action, abs_url, callback))
                return callback
            except Exception as e:
                exit("\033[31;1m%s\033[0m" % e)
