# -*- coding: utf-8 -*-
__author__ = 'CQ'
from core import client


class command_handler(object):

    def __init__(self, sys_args):
        self.sys_args = sys_args
        if len(self.sys_args) < 2:
            exit(self.help_msg())
        self.command_allowcator()

    def command_allowcator(self):
        '''分捡用户输入的不同指令'''
        if hasattr(self, self.sys_args[1]):
            func = getattr(self, self.sys_args[1])
            return func()
        else:
            print("命令错误或不存在!")
            self.help_msg()

    def help_msg(self):
        valid_commands = '''
        start       运行客户端代理
        stop        停止客户端代理
        '''
        exit(valid_commands)

    def start(self):
        print("监控客户端代理准备运行。。。")
        #exit_flag = False

        Client = client.ClientHandle()
        Client.forever_run()

    def stop(self):
        print("监控客户端代理停止运行。。。")

