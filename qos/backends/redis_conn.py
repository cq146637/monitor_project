# -*- coding: utf-8 -*-
__author__ = 'CQ'

import redis


def redis_conn(django_settings):
    pool = redis.ConnectionPool(host=django_settings.REDIS_CONN['HOST'],
                                port=django_settings.REDIS_CONN['PORT'],
                                password=django_settings.REDIS_CONN['PASSWD'],
                                )
    obj = redis.Redis(connection_pool=pool)
    return obj
