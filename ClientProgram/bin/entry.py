# -*- coding: utf-8 -*-
__author__ = 'CQ'

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from core import main

if '__main__' == __name__:
    client = main.command_handler(sys.argv)

