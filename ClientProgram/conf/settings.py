# -*- coding: utf-8 -*-
__author__ = 'CQ'

configs = {
    "HostID": 2,
    "Server": "202.207.178.209",
    "ServerPort": 8000,
    "urls": {
        "get_host_id": ['monitor/get_host_id/', 'get'],
        "send_host_sysinfo": ['monitor/api/client/sysinfo/', 'post'],
        "get_configs": ["monitor/api/client/config", 'get'],
        "service_report": ["monitor/api/client/service/report/", 'post']
    },
    "RequestTimeout": 30,
    "ConfigUpdateInterval": 300,  # 5 min 获取一次监控配置文件
}
