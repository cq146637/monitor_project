# -*- coding: utf-8 -*-
__author__ = 'CQ'

import subprocess
import time


def update_host_status(obj):
    global_monitor_dic = obj.global_monitor_dic
    print(global_monitor_dic)
    for host, val in global_monitor_dic.items():
        if "keepalive" in val.keys():
            cmd = "ping -n 1 %s" % '0.0.0.0'
            out, exitcode, err = sys_command_outstatuserr(cmd, 0.5)
            if exitcode == 128 or exitcode != 0 or b'\xd7\xd6\xbd\xda=32' not in out:
                print("主机[%s]失活")
                host.status = 3
                host.save()
                msg = '''The host [%s] died  ...''' % host.name
                obj.trigger_notifier(host_obj=host, trigger_id=None, positive_expressions=None, msg=msg)
            else:
                host_alive_key = 'HostAliveFlag_%s' % host.id
                obj.redis.set(host_alive_key, time.time())
                obj.redis.expire(host_alive_key, 3)


def sys_command_outstatuserr(cmd, timeout=0.5):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    t_beginning = time.time()
    while True:
        if p.poll() is not None:
            res = p.communicate()
            exitcode = p.poll() if p.poll() else 0
            return res[0], exitcode, res[1]
        seconds_passed = time.time() - t_beginning
        if timeout and seconds_passed > timeout:
            p.terminate()
            out, exitcode, err = '', 128, '执行系统命令超时'
            print(err)
            return out, exitcode, err
