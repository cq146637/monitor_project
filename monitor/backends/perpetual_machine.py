# -*- coding: utf-8 -*-
__author__ = 'CQ'

import sys
import os
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "untitled.settings")
from untitled import settings

django.setup()
from monitor.backends import data_processing


def main():
    reactor = data_processing.DataHandler(settings)
    reactor.looping()


if __name__ == '__main__':
    main()






