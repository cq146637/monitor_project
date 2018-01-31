# -*- coding: utf-8 -*-
__author__ = 'CQ'

import time
import json
import pickle
from monitor import models
from monitor.backends import redis_conn
import operator
import redis
from monitor.backends import keepalive
import threading


class DataHandler(object):

    def __init__(self, django_settings, connect_redis=True):
        self.django_settings = django_settings
        self.poll_interval = 3  # 每3秒进行一次全局轮询,也是主机存活监测时间
        self.config_update_interval = 120  # 每120s重新从数据库加载一次配置数据
        self.config_last_loading_time = time.time()
        self.global_monitor_dic = {}
        self.exit_flag = False
        if connect_redis:
            self.redis = redis_conn.redis_conn(django_settings)

    def looping(self):
        """
        start looping data ...
        检测所有主机需要监控的服务的数据有没有按时汇报上来，只做基本检测
        :return:
        """
        # get latest report data
        self.update_or_load_configs()  # 生成全局的监控配置dict
        count = 0
        while not self.exit_flag:
            print("looping %s".center(50, '-') % count)
            count += 1
            # 线程独自判断主机是否存活
            t = threading.Thread(target=keepalive.update_host_status, args=(self, ))
            t.start()
            if time.time() - self.config_last_loading_time >= self.config_update_interval:
                print("\033[41;1mneed update configs ...\033[0m")
                self.update_or_load_configs()
                # print("monitor dic", self.global_monitor_dic)
            if self.global_monitor_dic:
                for host, config_dic in self.global_monitor_dic.items():
                    print('handling host:\033[32;1m%s\033[0m' % host)
                    # 循环所有要监控的服务
                    for service_id, val in config_dic['services'].items():
                        # print(service_id,val)
                        service_obj, last_monitor_time = val
                        # reached the next monitor interval
                        # 初始化时给定0，所以监控一开始就立马刷新主机服务列表
                        if time.time() - last_monitor_time >= service_obj.interval:
                            print("\033[33;1mserivce [%s] has reached the monitor interval..\033[0m" % service_obj.name)
                            self.global_monitor_dic[host]['services'][service_obj.id][1] = time.time()
                            # self.load_service_data_and_calulating(h,service_obj)
                            # only do basic data validataion here, alert if the client didn't report data to server in \
                            # the configured time interval
                            self.data_point_validation(host, service_obj)  # 检测此服务最近的汇报数据
                        else:
                            next_monitor_time = time.time() - last_monitor_time - service_obj.interval
                            print("service [%s] next monitor time is %s" % (service_obj.name, next_monitor_time))

                    if time.time() - self.global_monitor_dic[host]['status_last_check'] > 10:
                        # 检测有没有这个机器的trigger,如果没有,把机器状态改成ok
                        trigger_redis_key = "host_%s_trigger*" % host.id
                        trigger_keys = self.redis.keys(trigger_redis_key)
                        # print('len grigger keys....',trigger_keys)
                        if len(trigger_keys) == 0:  # 没有trigger被触发,可以把状态改为ok了
                            host.status = 1
                            host.save()
                    # looping triggers 这里是真正根据用户的配置来监控了
                    # for trigger_id,trigger_obj in config_dic['triggers'].items():
                    #    print("triggers expressions:",trigger_obj.triggerexpression_set.select_related())
                    #    self.load_service_data_and_calulating(h,trigger_obj)

            time.sleep(self.poll_interval)

    def data_point_validation(self, host_obj, service_obj):
        """
        only do basic data validation here, alert if the client didn't report data to server in the configured time interval
        :param host_obj:
        :param service_obj:
        :return:
        """
        # 拼出此服务在redis中存储的对应key
        service_redis_key = "StatusData_%s_%s_latest" % (host_obj.id, service_obj.name)
        latest_data_point = self.redis.lrange(service_redis_key, -1, -1)
        # data list is not empty
        if latest_data_point:
            latest_data_point = json.loads(latest_data_point[0].decode())
            print("\033[41;1mlatest data point\033[0m %s" % latest_data_point)
            latest_service_data, last_report_time = latest_data_point
            monitor_interval = service_obj.interval + self.django_settings.REPORT_LATE_TOLERANCE_TIME
            # 超过监控间隔但数据还没汇报过来,something wrong with client
            if time.time() - last_report_time > monitor_interval:
                no_data_secs = time.time() - last_report_time
                msg = '''Some thing must be wrong with client [%s] , because haven't receive data of service [%s] \
                for [%s]s (interval is [%s])\033[0m''' % (host_obj.ip_addr, service_obj.name, no_data_secs,
                                                          monitor_interval)
                self.trigger_notifier(host_obj=host_obj, trigger_id=None, positive_expressions=None,
                                      msg=msg)
                print("\033[41;1m%s\033[0m" % msg)
                # if service_obj.name == 'uptime':  # 监控主机存活的服务
                #     host_obj.status = 3  # unreachable
                #     host_obj.save()
                # else:
                #     host_obj.status = 5  # problem
                #     host_obj.save()

        else:  # no data at all
            print("\033[41;1m no data for serivce [%s] host[%s] at all..\033[0m" % (service_obj.name, host_obj.name))
            msg = '''no data for serivce [%s] host[%s] at all..''' % (service_obj.name, host_obj.name)
            self.trigger_notifier(host_obj=host_obj, trigger_id=None, positive_expressions=None, msg=msg)
            host_obj.status = 5  # problem
            host_obj.save()
        # print("triggers:", self.global_monitor_dic[host_obj]['triggers'])

    def load_service_data_and_calulating(self, host_obj, trigger_obj, redis_obj):
        """
        fetching out service data from redis db and calculate according to each serivce's trigger configuration
        :param host_obj:
        :param trigger_obj:
        :param redis_obj: #从外面调用此函数时需传入redis_obj,以减少重复连接
        :return:
        """
        self.redis = redis_obj
        positive_expressions = []  # 触发报警的表达式
        expression_res_string = ''  # 判断报警表达式，True or Flase and Flase
        for expression in trigger_obj.triggerexpression_set.select_related().order_by('id'):
            # 实例化触发器表达式处理对象
            expression_process_obj = ExpressionProcess(self, host_obj, expression)
            # 得到单条expression表达式的结果
            single_expression_res = expression_process_obj.process()  # 结果返回一个字典
            if single_expression_res:  # 如果字典非空
                if single_expression_res['expression_obj'].logic_type:  # 且关联表达式不是最后一条
                    expression_res_string += str(single_expression_res['calc_res']) + ' ' + \
                                             single_expression_res['expression_obj'].logic_type + ' '
                else:
                    expression_res_string += str(single_expression_res['calc_res'])

                # 把所有结果为True的expression提出来,报警时你得知道是谁出问题导致trigger触发了
                if single_expression_res['calc_res'] is True:
                    # 要存到redis里,数据库对象转成id
                    single_expression_res['expression_obj'] = single_expression_res['expression_obj'].id
                    positive_expressions.append(single_expression_res)
                    # single expression不成立,随便加个东西,别让程序出错,这个地方我觉得是个bug
            else:
                expression_res_string += 'None'
        print("whole trigger res:", trigger_obj.name, expression_res_string)
        if expression_res_string:
            trigger_res = eval(expression_res_string)
            print("whole trigger res:", trigger_res)
            # 终于走到这一步,该触发报警了
            if trigger_res:
                print("##############trigger alert:", trigger_obj.severity, trigger_res)
                # msg 需要专门分析后生成, 这里是临时写的
                # trigger_notifier 触发报警函数
                self.trigger_notifier(host_obj, trigger_obj.id, positive_expressions, msg=trigger_obj.name)

    def update_or_load_configs(self):
        """
        load monitor configs from Mysql DB
        :return:
        """
        all_enabled_hosts = models.Host.objects.all()
        for h in all_enabled_hosts:
            if h not in self.global_monitor_dic:  # new host
                self.global_monitor_dic[h] = {'services': {}, 'triggers': {}}
                '''self.global_monitor_dic ={
                    'h1':{'services'{'cpu_id':[cpu_obj,0], # 'cpu’服务ID 0位置存放时间
                                     'mem_id':[mem_obj,0]
                                     },
                          'trigger':{t1:t1_obj,}
                          'keepalive': 0    # 当主机的状态为正常Online时才有
                        }
                }'''
            # 如果主机状态正常需要监控主机是否存活
            if h.status == 1:
                self.global_monitor_dic[h]['keepalive'] = time.time()
            service_list = []
            trigger_list = []
            for group in h.host_groups.select_related():
                # print("grouptemplates:", group.templates.select_related())
                for template in group.templates.select_related():
                    # print("tempalte:",template.services.select_related())
                    # print("triigers:",template.triggers.select_related())
                    service_list.extend(template.services.select_related())
                    trigger_list.extend(template.triggers.select_related())
                for service in service_list:
                    if service.id not in self.global_monitor_dic[h]['services']:  # first loop
                        self.global_monitor_dic[h]['services'][service.id] = [service, 0]
                    else:
                        self.global_monitor_dic[h]['services'][service.id][0] = service
                for trigger in trigger_list:
                    # if not self.global_monitor_dic['triggers'][trigger.id]:
                    self.global_monitor_dic[h]['triggers'][trigger.id] = trigger
            # print(h.templates.select_related() )
            # print('service list:',service_list)

            for template in h.templates.select_related():
                service_list.extend(template.services.select_related())
                trigger_list.extend(template.triggers.select_related())
            for service in service_list:
                if service.id not in self.global_monitor_dic[h]['services']:  # first loop
                    self.global_monitor_dic[h]['services'][service.id] = [service, 0]
                else:
                    self.global_monitor_dic[h]['services'][service.id][0] = service
            for trigger in trigger_list:
                self.global_monitor_dic[h]['triggers'][trigger.id] = trigger
            # print(self.global_monitor_dic[h])
            # 通过这个时间来确定是否需要更新主机状态
            self.global_monitor_dic[h].setdefault('status_last_check', time.time())

        self.config_last_loading_time = time.time()
        return True

    def trigger_notifier(self, host_obj, trigger_id, positive_expressions, msg=None, redis_obj=None):
        """
        all the triggers alerts need to be published through here
        :param host_obj:
        :param trigger_id:
        :param positive_expressions: it's list, contains all the expression has True result
        :param redis_obj:
        :return:
        """
        # alert.sendmail(msg)
        # alert.sendsms(msg)
        # 从外部调用 时才用的到,为了避免重复调用 redis连接
        if redis_obj:
            self.redis = redis_obj
        print("\033[43;1mgoing to send alert msg to trigger queue............\033[0m")
        # print('trigger_notifier argv:', host_obj, trigger_id, positive_expressions, redis_obj)
        msg_dic = {'host_id': host_obj.id,
                   'trigger_id': trigger_id,
                   'positive_expressions': positive_expressions,
                   'msg': msg,
                   'time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                   'start_time': time.time(),
                   'duration': None
                   }
        self.redis.publish(self.django_settings.TRIGGER_CHAN, pickle.dumps(msg_dic))

        # 先把之前的trigger加载回来,获取上次报警的时间,以统计故障持续时间
        trigger_redis_key = "host_%s_trigger_%s" % (host_obj.id, trigger_id)
        old_trigger_data = self.redis.get(trigger_redis_key)
        if old_trigger_data:
            old_trigger_data = old_trigger_data.decode()
            trigger_startime = json.loads(old_trigger_data)['start_time']
            msg_dic['start_time'] = trigger_startime
            msg_dic['duration'] = round(time.time() - trigger_startime)

        # 同时在redis中纪录这个trigger , 前端页面展示时要统计trigger个数
        # 一个trigger 纪录 5分钟后会自动清除, 为了在前端统计trigger个数用的
        self.redis.set(trigger_redis_key, json.dumps(msg_dic), 300)


class ExpressionProcess(object):
    """
    load data and calc it by different method
    """
    def __init__(self, main_ins, host_obj, expression_obj, specified_item=None):
        """
        :param main_ins:   DataHandler 实例
        :param host_obj: 具体的host obj
        :param expression_obj:
        :return:
        计算单条表达式的结果
        """
        self.host_obj = host_obj
        self.expression_obj = expression_obj
        self.main_ins = main_ins
        # 拼出此服务在redis中存储的对应key
        self.service_redis_key = "StatusData_%s_%s_latest" % (host_obj.id, expression_obj.service.name)
        # 获取要从redis中取多长时间的数据,单位为minute
        self.time_range = self.expression_obj.operator_calc_args.split(',')[0]
        print("\033[31;1m------%s [%s]------\033[0m" % (self.service_redis_key, self.expression_obj.service_items.key))

    def load_data_from_redis(self):
        """load data from redis according to expression's configuration"""
        # 时间段是指每X分钟内的特征数据（特征数据：X分钟内平均数值或最大数值或最小数值或中位数）
        time_in_sec = int(self.time_range) * 60
        # 下面的+60是默认多取一分钟数据,多出来的后面会去掉，也是先大概确定要取数据的多少，后面再过滤就比较轻松了
        approximate_data_points = (time_in_sec + 60) / self.expression_obj.service.interval  # 获取一个大概要取的数量
        try:
            data_range_raw = self.main_ins.redis.lrange(self.service_redis_key, -int(approximate_data_points), -1)
        except redis.exceptions.ResponseError:
            print("列表中数据个数不满足计算要求")
            data_range_raw = self.main_ins.redis.lrange(self.service_redis_key, 0, -1)

        approximate_data_range = [json.loads(i.decode()) for i in data_range_raw]
        data_range = []  # 精确的需要的数据列表
        for point in approximate_data_range:
            val, saving_time = point
            if time.time() - saving_time < time_in_sec:  # 代表数据是判断触发报警的有效数据
                if val:  # 确保数据存在
                    data_range.append(point)
                    """
                    if 'data' not in val:  # 代表这个dict没有sub_dict
                        print("\033[44;1m%s\033[0m" % val[self.expression_obj.service_index.key])
                        # 如何处理这些数据 呢? 是求avg(5), hit(5,3)....? 看来只能把数据集合交给不同的方法去处理了
                        # self.process(self.)
                        # data_range.append(
                    else:  # 像disk , nic这种有多个item的数据
                        for k, v in val['data'].items():
                            print("\033[45;1m%s, %s\033[0m" % (k, v))
                            print("\033[45;1m%s, %s\033[0m" % (k, v[self.expression_obj.service_index.key]))
                    """
        return data_range

    def process(self):
        """算出单条expression表达式的结果"""
        # 按照用户的配置把数据从redis里取出来了, 比如 最近5分钟,或10分钟的数据
        data_list = self.load_data_from_redis()
        data_calc_func = getattr(self, 'get_%s' % self.expression_obj.data_calc_func)
        # 返回结果列表[True,43,None][是否触发报警,特征数据,报警网卡或None]
        single_expression_calc_res = data_calc_func(data_list)
        # print("---res of single_expression_calc_res ", single_expression_calc_res)
        if single_expression_calc_res:  # 确保上面的条件有正确的返回
            res_dic = {
                'items': self.expression_obj.service_items.name,
                'calc_res': single_expression_calc_res[0],
                'operator_type': self.expression_obj.operator_type,
                'calc_res_val': single_expression_calc_res[1],
                'severity': self.expression_obj.trigger.severity,
                'service_item': single_expression_calc_res[2],  # 网卡或者None
                'expression_obj': self.expression_obj
            }
            print("\033[41;1msingle_expression_calc_res:%s\033[0m" % res_dic)
            return res_dic
        else:
            return False

    def get_avg(self, data_set):
        """
        return average value of given data set
        :param data_set:
        :return:
        """
        clean_data_list = []   # 存储监控指标对应数据
        clean_data_dic = {}    # 每个表达式外键关联一个服务指标，只需要判断这一个服务指标是否超过阈值
        for point in data_set:
            val, save_time = point
            if val:
                if 'data' not in val:  # 非网卡监控数据
                    clean_data_list.append(val[self.expression_obj.service_items.key])

                else:  # 网卡监控数据
                    for k, v in val['data'].items():  # k是网卡名
                        if k not in clean_data_dic:
                            clean_data_dic[k] = []
                        clean_data_dic[k].append(v[self.expression_obj.service_items.key])

        if clean_data_list:  # 如果list非空说明该表达式对应非网卡服务
            clean_data_list = [float(i) for i in clean_data_list]
            # avg_res = 0 if sum(clean_data_list) == 0 else  sum(clean_data_list)/ len(clean_data_list)
            avg_res = sum(clean_data_list) / len(clean_data_list)
            print("\033[46;1mres [%s] [%s] [%s] = %s\033[0m" % (avg_res,
                                                                self.expression_obj.operator_type,
                                                                self.expression_obj.threshold,
                                                                self.judge(avg_res)))
            return [self.judge(avg_res), avg_res, None]
        elif clean_data_dic:  # 如果dic非空说明该表达式对应网卡服务，网卡服务无非多了一层字典
            for k, v in clean_data_dic.items():
                clean_v_list = [float(i) for i in v]  # 将字符串转换为浮点数
                avg_res = 0 if sum(clean_v_list) == 0 else sum(clean_v_list) / len(clean_v_list)
                # print("\033[46;1m-%s---avg res:%s\033[0m" % (k, avg_res))
                print("\033[46;1mres [%s] [%s] [%s] [%s] = %s\033[0m" % (k,
                                                                         avg_res,
                                                                         self.expression_obj.operator_type,
                                                                         self.expression_obj.threshold,
                                                                         self.judge(avg_res),))

                if self.expression_obj.specified_item_key:  # 监控了特定的指标,比如有多个网卡,但这里只特定监控eth0
                    if k == self.expression_obj.specified_index_key:  # 就是监控这个特定指标,match上了
                        # 在这里判断特定网卡是否超越阈值
                        calc_res = self.judge(avg_res)
                        print('specified monitor key:', self.expression_obj.specified_item_key)
                        if calc_res:
                            return [calc_res, avg_res, k]  # 指定监控网卡已经超过阈值
                else:  # 监控这个服务的所有项, 比如一台机器的多个网卡, 任意一个超过了阈值,都 算是有问题的
                    calc_res = self.judge(avg_res)
                    if calc_res:
                        return [calc_res, avg_res, k]
                # print('clean data dic:', k, len(clean_v_list), clean_v_list)
            else:  # 能走到这一步,代表 上面的循环判段都未成立
                return [False, -1, None]
        else:  # 可能是由于最近这个服务 没有数据 汇报 过来,取到的数据 为空,所以没办法 判断阈值
            return [False, None, None]

    def judge(self, calculated_val):
        """
        determine whether the index has reached the alert benchmark
        :param calculated_val: 已经算好的结果,可能是avg(5) or ....
        :return:
        """
        # expression_args = self.expression_obj.data_calc_args.split(',')
        # hit_times = expression_args[1] if len(expression_args)>1 else None
        # if hit_times:  # 定义了超过阈值几次的条件
        calc_func = getattr(operator, self.expression_obj.operator_type)
        # calc_func = operator.eq....
        return calc_func(calculated_val, self.expression_obj.threshold)

    def get_hit(self, data_set):
        """
        return hit times  value of given data set
        :param data_set:
        :return:
        """
        pass
