# -*- coding: utf-8 -*-
__author__ = 'CQ'

import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "untitled.settings")

import django
django.setup()

from untitled import settings
from django.core.mail import send_mail

send_mail(
    '啊啊啊啊啊啊',
    'hello worlds cdb quit ipdb-20140902-99884.txt bbb ccawfwe啊啊啊 awfgwag aw gwasf',
    'cq146637@163.com',
    ['1016025625@qq.com'],
)
