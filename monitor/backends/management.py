# -*- coding: utf-8 -*-
__author__ = 'CQ'

import os
import sys
import django

django.setup()
from monitor.backends import perpetual_machine, trigger_handler

from untitled import settings


class ManagementUtility(object):
    """
    负责处理触发报警队列，通过Redis订阅获取发布消息
    """
    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]
        self.prog_name = os.path.basename(self.argv[0])
        self.settings_exception = None
        self.registered_actions = {
            'start': self.start,
            'stop': self.stop,
            'trigger_watch': self.trigger_watch,
        }
        self.argv_check()

    def argv_check(self):
        """
        do basic validation argv checks
        :return:
        """
        if len(self.argv) < 2:
            self.main_help_text()
        if self.argv[1] not in self.registered_actions:
            self.main_help_text()
        else:
            self.registered_actions[sys.argv[1]]()

    def start(self):
        """start monitor server frontend and backend"""
        perpetual_machine.main()

    def stop(self):
        """stop monitor server"""

    def trigger_watch(self):
        """start to listen triggers"""
        trigger_watch = trigger_handler.TriggerHandler(settings)
        trigger_watch.start_watching()

    def main_help_text(self, commands_only=False):
        """
        Returns the script's main help text, as a string.
        """
        if not commands_only:
            print("supported commands as flow:")
            for k, v in self.registered_actions.items():
                print("    %s%s" % (k.ljust(20), v.__doc__))
            exit()

    def execute(self):
        """
        run according to user's input
        :return:
        """


def execute_from_command_line(argv=None):
    """
    A simple method that runs a ManagementUtility.
    """
    utility = ManagementUtility(argv)
    utility.execute()
