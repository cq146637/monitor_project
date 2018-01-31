# -*- coding: utf-8 -*-
__author__ = 'CQ'

from untitled import settings
import time
import json
import copy
import math
from monitor import models
import redis


class DataStore(object):
    """
    processing the client reported service data , do some data optimiaztion and save it into redis DB
    处理客户端报告数据，并做数据优化
    """
    def __init__(self, client_id, service_name, data, redis_obj):
        """
        :param client_id:
        :param service_name:
        :param data: the client reported service clean data ,
        :return:
        """
        self.client_id = client_id
        self.service_name = service_name
        self.data = data
        self.redis_conn_obj = redis_obj
        self.process_and_save()

    def get_count_lastest(self, optimization_interval):
        """
        用优化周期除于服务报告周期，即可知道即将一次对实时列表中的多少个数据做优化
        向上整除法不会影响优化精度，这样可以一次过滤大量的数据，后面只需要再判断时间戳就好了
        :param optimization_interval:
        :return:
        """
        server_interval = models.Service.objects.filter(name=self.service_name).values('interval').first()['interval']
        return math.ceil(optimization_interval/int(server_interval))

    def get_data_slice(self, lastest_data_key, optimization_interval):
        """
        优化数据，例如：对十分钟内的实时数据求和取平均值，然后将平均值存到10分钟列表中的最后一个
        :param optimization_interval: e.g: 600, means get latest 10 mins real data from redis
        :return:
        """
        count = self.get_count_lastest(optimization_interval)
        # 即使在刚开始监控的时候，数据量可能不够
        try:
            all_real_data = self.redis_conn_obj.lrange(lastest_data_key, -count, -1)
        except redis.exceptions.ResponseError:
            print("列表中数据个数不满足计算要求")
            all_real_data = self.redis_conn_obj.lrange(lastest_data_key, 0, -1)

        data_set = []
        for item in all_real_data:
            # print(json.loads(item))
            # Redis获取的数据是字节，utf-8的编码，而数据报告时原来是json字符串，所以需要转换一下才能成为原来的字典类型
            data = json.loads(item.decode())
            # 即使获取到了实时数据，但没有判断它们是否在优化周期内，如果不在优化周期内说明已经被上个优化周期处理过了
            if len(data) == 2:
                service_data, last_save_time = data
                if time.time() - last_save_time <= optimization_interval:
                    data_set.append(data)
                else:
                    pass
        return data_set

    def process_and_save(self):
        '''
        processing data and save into redis
        :return:
        '''
        print("-----------------------数据优化中-----------------------")
        # service data is valid
        if self.data['status'] == 0:
            # 获取预先定义好的优化方案
            for key, data_series_val in settings.STATUS_DATA_OPTIMIZATION.items():
                data_series_optimize_interval, max_data_point = data_series_val
                # 组成Redis键名
                data_series_key_in_redis = "StatusData_%s_%s_%s" % (self.client_id, self.service_name, key)
                # Example: data_series_key_in_redis = StatusData_1_LinuxNetwork_t_in
                last_point_from_redis = self.redis_conn_obj.lrange(data_series_key_in_redis, -1, -1)
                if not last_point_from_redis:
                    # this key is not exist in redis
                    # 刚开始监控的时候列表中还没有数据，需要初始化一个空的数据+时间戳，
                    # 并初始化Redis's Key
                    self.redis_conn_obj.rpush(data_series_key_in_redis, json.dumps([None, time.time()]))
                if data_series_optimize_interval == 0:
                    # 只要时间为0，说明这是最新发送的监控数据，需要马上存储到Redis中
                    self.redis_conn_obj.rpush(data_series_key_in_redis, json.dumps([self.data, time.time()]))

                else:
                    # 取最新的存储数据，用当前时间戳相减，判断是否达到优化时间，如果达到则执行优化操作
                    # last_point_data = 监控数据 last_point_save_time = 时间戳
                    last_point_data, last_point_save_time =  \
                        json.loads(self.redis_conn_obj.lrange(data_series_key_in_redis, -1, -1)[0].decode())

                    if time.time() - last_point_save_time >= data_series_optimize_interval:
                        # 获取实时列表数据，用这里面的数据做优化，即对固定时间段内数据求和取平均值存储到对应的优化列表中
                        lastest_data_key_in_redis = "StatusData_%s_%s_latest" % (self.client_id, self.service_name)
                        print("calulating data for key:\033[31;1m%s\033[0m" % data_series_key_in_redis)
                        # 获取准备优化的数据，例：对于20mins的列表，服务监控定时为60s的
                        # 需要取1200/60个实时数据，然后对它们求和取平均值，将优化结果存储到20mins的列表的末尾
                        data_set = self.get_data_slice(lastest_data_key_in_redis, data_series_optimize_interval)
                        print('--------------------------len dataset :', len(data_set))
                        if len(data_set) > 0:
                            # 接下来拿这个data_set交给下面这个方法,让它算出优化的结果 来
                            optimized_data = self.get_optimized_data(data_series_key_in_redis, data_set)
                            # 只要优化结果不为空就将它存储至相应列表末尾
                            if optimized_data:
                                self.save_optimized_data(data_series_key_in_redis, optimized_data)

                # 同时确保数据在redis中的存储数量不超过settings中指定 的值
                if self.redis_conn_obj.llen(data_series_key_in_redis) >= max_data_point:
                    self.redis_conn_obj.lpop(data_series_key_in_redis)
                    # 删除最旧的一个数据
        else:
            print("report data is invalid::", self.data)
            raise ValueError

    def save_optimized_data(self, data_series_key_in_redis, optimized_data):
        '''
        save the optimized data into db
        :param optimized_data:
        :return:
        '''
        # 优化后的数据与实施数据存储格式不一样
        # 实时数据每个监控指标对应一个数值
        # 优化数据每个监控指标对应一个列表，列表中元素分别对应[平均值、最大值、最小值、中位数]
        self.redis_conn_obj.rpush(data_series_key_in_redis, json.dumps([optimized_data, time.time()]))

    def get_optimized_data(self, data_set_key, raw_service_data):
        '''
        calculate out ava,max,min,mid value from raw service data set
        :param data_set_key: where the optimized data needed to save to in redis db
        :param raw_service_data: raw service data data list
        :return:
        '''
        # index_init =[avg,max,min,mid]
        # print("get_optimized_data:", raw_service_data[0])
        # [iowait, idle,system...]
        # [0] 列表中第一个列表 [0] 代表data
        service_data_keys = raw_service_data[0][0].keys()
        # use this to build up a new empty dic
        first_service_data_point = raw_service_data[0][0]
        optimized_dic = {}  # 为优化数据准备字典
        if 'data' not in service_data_keys:
            # means this dic has  no subdic, works for service like cpu,memory
            # 当前存储有两种数据格式，非网络监控数据data下面直接是监控指标和数值
            # 网络监控数据data下还是一个data，里面是网卡，网卡下才是监控指标和数值
            for key in service_data_keys:
                optimized_dic[key] = []
            # 该字典将要将每条记录中的指标分类存放
            # tmp_data_dic {
            #       "idle":[xx,xxx,xxx,x,...],
            #       "system":[xxx,x,x,x,x,],
            #       ...
            # }
            # 为了临时存最近n分钟的数据 ,把它们按照每个指标 都 搞成一个一个列表 ,来存最近N分钟的数据
            tmp_data_dic = copy.deepcopy(optimized_dic)
            # loop 最近n分钟的数据
            for service_data_item, last_save_time in raw_service_data:
                # loop 每个数据点的指标
                for service_item, v in service_data_item.items():
                    try:
                        # 把这个点的当前这个指标 的值 添加到临时dict中
                        # 对每个数据保留到小数点后两位
                        tmp_data_dic[service_item].append(round(float(v), 2))
                    except ValueError:
                        pass
            for service_k, v_list in tmp_data_dic.items():
                print(service_k, v_list)
                avg_res = self.get_average(v_list)
                max_res = self.get_max(v_list)
                min_res = self.get_min(v_list)
                mid_res = self.get_mid(v_list)
                optimized_dic[service_k] = [avg_res, max_res, min_res, mid_res]

        else:
            # has sub dic inside key 'data', works for a service has multiple independent items,
            # like many ethernet,disks...
            # print("**************>>>",first_service_data_point )
            for service_item_key, v_dic in first_service_data_point['data'].items():
                # service_item_key 相当于lo,eth0,... , v_dic ={ t_in:333,t_out:3353}
                optimized_dic[service_item_key] = {}
                for k2, v2 in v_dic.items():
                    # {etho0:{t_in:[],t_out:[]}}
                    optimized_dic[service_item_key][k2] = []

            tmp_data_dic = copy.deepcopy(optimized_dic)
            # some times this tmp_data_dic might be empty due to client report err
            if tmp_data_dic:
                # loop最近n分钟数据
                for service_data_item, last_save_time in raw_service_data:
                    for service_index, val_dic in service_data_item['data'].items():
                        # service_index这个值 相当于eth0,eth1...
                        for service_item_sub_key, val in val_dic.items():
                            # 上面这个service_item_sub_key相当于t_in,t_out
                            tmp_data_dic[service_index][service_item_sub_key].append(round(float(val), 2))
                            # 上面的service_index变量相当于 eth0...
                for service_k, v_dic in tmp_data_dic.items():   # 这层循环网卡lo、ens33、eth0、br0
                    for service_sub_k, v_list in v_dic.items():  # 这层循环网卡监控指标
                        print(service_k, service_sub_k, v_list)
                        avg_res = self.get_average(v_list)
                        max_res = self.get_max(v_list)
                        min_res = self.get_min(v_list)
                        mid_res = self.get_mid(v_list)
                        optimized_dic[service_k][service_sub_k] = [avg_res, max_res, min_res, mid_res]
                        print(service_k, service_sub_k, optimized_dic[service_k][service_sub_k])
            else:
                print("\033[41;1mMust be sth wrong with client report data\033[0m")
        # print("optimized empty dic:", optimized_dic)
        return optimized_dic

    def get_average(self, data_set):
        '''
        calc the avg value of data set
        :param data_set:
        :return:
        '''
        if len(data_set) > 0:
            return sum(data_set) / len(data_set)
        else:
            return 0

    def get_max(self, data_set):
        '''
        calc the max value of the data set
        :param data_set:
        :return:
        '''
        if len(data_set) > 0:
            return max(data_set)
        else:
            return 0

    def get_min(self, data_set):
        '''
        calc the minimum value of the data set
        :param data_set:
        :return:
        '''
        if len(data_set) > 0:
            return min(data_set)
        else:
            return 0

    def get_mid(self, data_set):
        '''
        calc the mid value of the data set
        :param data_set:
        :return:
        '''
        data_set.sort()
        # [1,4,99,32,8,9,4,5,9]
        # [1,3,5,7,9,22,54,77]
        if len(data_set) > 0:
            return data_set[int(len(data_set)/2)]
        else:
            return 0
