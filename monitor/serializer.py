# -*- coding: utf-8 -*-
__author__ = 'CQ'


from monitor import models
import json, time
from django.core.exceptions import ObjectDoesNotExist


class ClientHandler(object):

    def __init__(self, client_id):
        self.client_id = client_id
        self.client_configs = {
            "services": {}
        }

    def fetch_configs(self):
        try:
            host_obj = models.Host.objects.get(id=self.client_id)
            # prefetch_related多次查询获取templates和关联对象
            templates_list = list(host_obj.templates.prefetch_related())
            # templates_list = list(host_obj.select_related())

            for host_group in host_obj.host_groups.prefetch_related():
                templates_list.extend(host_group.templates.prefetch_related())

            for template in templates_list:
                for service in template.services.select_related():
                    # 将模板中的服务取出，self.client_configs是要发送给客户端的监控服务汇总
                    self.client_configs['services'][service.name] = [service.plugin_name, service.interval]

        except ObjectDoesNotExist:
            pass

        # 这里返回给客户端的数据格式为{'services':{"LinuxMemory":['GetLinuxMemStatus', 90], "LinuxNetwork":[ ... ]}}
        return self.client_configs


def get_host_triggers(host_obj):
    triggers = []
    for template in host_obj.templates.select_related():
        triggers.extend(template.triggers.select_related())
    for group in host_obj.host_groups.select_related():
        for template in group.templates.select_related():
            triggers.extend(template.triggers.select_related())
    # 设置成集合，去重复触发器对象
    return set(triggers)


class StatusSerializer(object):

    def __init__(self, request, redis):
        self.request = request
        self.redis = redis

    def by_hosts(self):
        """
        serialize all the hosts
        :return:
        """
        host_obj_list = models.Host.objects.all()
        host_data_list = []
        for h in host_obj_list:
            host_data_list.append( self.single_host_info(h))
        return host_data_list

    def single_host_info(self,host_obj):
        """
        serialize single host into a dic
        :param host_obj:
        :return:
        """
        data = {
            'id': host_obj.id,
            'name': host_obj.name,
            'ip_addr': host_obj.ip_addr,
            'status': host_obj.get_status_display(),
            'uptime': None,
            'last_update': None,
            'total_services': None,
            'ok_nums': None,

        }
        # for uptime
        uptime = self.get_host_uptime(host_obj)
        self.get_triggers(host_obj)
        if uptime:
            print('uptime:',uptime)
            data['uptime'] = uptime[0]['uptime']
            print('mktime :',time.gmtime(uptime[1]))
            data['last_update'] = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(uptime[1]))

        # for triggers
        data['triggers'] = self.get_triggers(host_obj)
        return data

    def get_host_uptime(self,host_obj):
        """
        get host uptime data
        :param host_obj:
        :return:
        """
        redis_key = 'StatusData_%s_uptime_latest' % host_obj.id
        last_data_point = self.redis.lrange(redis_key, -1, -1)
        if last_data_point:
            # print('----last updtime point:',last_data_point[0])
            last_data_point, last_update = json.loads(last_data_point[0])
            return last_data_point, last_update

    def get_triggers(self, host_obj):
        trigger_keys = self.redis.keys("host_%s_trigger_*" % host_obj.id)
        # print('trigger keys:',trigger_keys)
        ''' (1,'Information'),
        (2,'Warning'),
        (3,'Average'),
        (4,'High'),
        (5,'Diaster'), '''
        trigger_dic = {
            1: [],
            2: [],
            3: [],
            4: [],
            5: []
        }

        for trigger_key in trigger_keys:
            trigger_data = self.redis.get(trigger_key)
            print("trigger_key", trigger_key)
            if trigger_key.decode().endswith("None"):
                trigger_dic[4].append(json.loads(trigger_data.decode()))
            else:
                trigger_id = trigger_key.decode().split('_')[-1]
                trigger_obj = models.Trigger.objects.get(id=trigger_id)
                trigger_dic[trigger_obj.severity].append(json.loads(trigger_data.decode()))
        # print('triiger data',trigger_dic)
        return trigger_dic


class GroupStatusSerializer(object):

    def __init__(self, request, redis):
        self.request = request
        self.redis = redis

    def get_all_groups_status(self):
        data_set = []  # store all groups status
        group_objs = models.HostGroup.objects.all()

        for group in group_objs:

            group_data = {
                # 'group_id':
                'hosts': [],
                'services': [],
                'triggers': [],
                'events': {'diaster': [],
                           'high': [],
                           'average': [],
                           'warning': [],
                           'info': []},
                'last_update': None
            }

            host_list = group.host_set.all()

            template_list = []
            service_list = []

            template_list.extend(group.templates.all())

            for host_obj in host_list:
                template_list.extend(host_obj.templates.select_related())
            # print("group ",group.name,template_list)

            template_list = set(template_list)

            for template_obj in template_list:
                service_list.extend(template_obj.services.all())

            service_list = set(service_list)
            # print("service",service_list)
            group_data['hosts'] = [{'id': obj.id} for obj in set(host_list)]
            group_data['services'] = [{'id': obj.id} for obj in set(service_list)]
            # print(group_data)
            group_data['group_id'] = group.id
            data_set.append(group_data)
        print(json.dumps(data_set))
