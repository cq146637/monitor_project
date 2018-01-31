# -*- coding: utf-8 -*-
__author__ = 'CQ'

from django.shortcuts import HttpResponse, render, redirect
import json
from monitor.serializer import ClientHandler, get_host_triggers
from django.views.decorators.csrf import csrf_exempt
from untitled import settings
from monitor.backends import redis_conn
from monitor.backends import data_optimization
from monitor.backends import data_processing
from monitor import serializer
import time
from monitor import models
from monitor import graphs
from monitor.backends import keepalive


# 由于所有的报告数据都需要存储在Redis中，所以这里生成一个数据库操作对象，整个程序只需要使用它就可以了，节省维护开销
REDIS_OBJ = redis_conn.redis_conn(settings)
# 生成探测器监测客户端是否存活


def client_configs(request, client_id):
    """
    发送监控配置给客户端
    :param request:
    :param client_id:
    :return:
    """
    config_obj = ClientHandler(client_id)  # 实例化一个客户端处理对象，并传入主机ID
    config = config_obj.fetch_configs()  # 抓取主机和主机组对应的服务

    if config:  # 不为空则返回
        return HttpResponse(json.dumps(config))


@csrf_exempt
def service_data_report(request):
    """
    处理客户端发送的服务监控报告，由于是POST请求所有需要处理CSRF，这里就使用@csrf_exempt，略去不考虑了
    :param request:
    :return:
    """
    if request.method == 'POST':
        try:
            print('---->host=%s, service=%s' % (request.POST.get('client_id'), request.POST.get('service_name')))
            data = json.loads(request.POST['data'])
            # StatusData_1_memory_latest
            client_id = request.POST.get('client_id')
            service_name = request.POST.get('service_name')

            # 每接收到一次服务监控报告都要触发一次数据优化,符合优化标准将优化
            # data_saveing_obj = data_optimization.DataStore(client_id, service_name, data, REDIS_OBJ)
            data_optimization.DataStore(client_id, service_name, data, REDIS_OBJ)

            # 由于DataStore已经为实时数据做过存储这里还往列表首部塞数据不知道为什么先注释了
            # redis_key_format为Redis中KEY的格式，最新的数据不需要存储优化
            # redis_key_format = "StatusData_%s_%s_latest" % (client_id, service_name)
            # data['report_time'] = time.time()
            # 将客户端发来的最新报告存储在Redis中
            # REDIS_OBJ.lpush(redis_key_format, json.dumps(data))

            # 在这里同时触发监控(在这里触发的好处是什么呢？)
            # 实时监控触发报警系统
            host_obj = models.Host.objects.get(id=client_id)
            service_triggers = get_host_triggers(host_obj)

            trigger_handler = data_processing.DataHandler(settings, connect_redis=False)
            for trigger in service_triggers:    # 循环主机关联的触发器，判断是否报警被触发
                trigger_handler.load_service_data_and_calulating(host_obj, trigger, REDIS_OBJ)
            print("service trigger:", service_triggers)

            # 順便更新主机存活状态
            host_alive_key = "HostAliveFlag_%s" % client_id
            REDIS_OBJ.set(host_alive_key, time.time())
            REDIS_OBJ.expire(host_alive_key, 3)
        except IndexError as e:
            print('----->err:', e)

    return HttpResponse(json.dumps("{'success':1,'data':'report success'}"))


def get_host_id(request):
    try:
        ip = request.META['HTTP_X_FORWARDED_FOR']
    except KeyError:
        ip = request.META['REMOTE_ADDR']
    print(ip)
    return HttpResponse(ip)


def dashboard(request):

    return render(request, 'monitor/dashboard.html')


def triggers(request):

    return render(request, 'monitor/triggers.html')


def hosts(request):
    host_list = models.Host.objects.all()
    last_time = time.ctime()
    print("hosts:", host_list)
    return render(request, 'monitor/hosts.html', {'host_list': host_list, 'last_time': last_time})


def host_detail(request, host_id):
    host_obj = models.Host.objects.get(id=host_id)
    return render(request, 'monitor/host_detail.html', {'host_obj': host_obj})


def host_detail_old(request, host_id):
    host_obj = models.Host.objects.get(id=host_id)
    config_obj = ClientHandler(host_obj.id)
    monitored_services = {
            "services": {},
            "sub_services": {}  # 存储一个服务有好几个独立子服务 的监控,比如网卡服务 有好几个网卡
        }

    template_list = list(host_obj.templates.select_related())

    for host_group in host_obj.host_groups.select_related():
        template_list.extend(host_group.templates.select_related() )
    print(template_list)
    for template in template_list:
        # print(template.services.select_related())
        for service in template.services.select_related():  # loop each service
            print(service)
            if not service.has_sub_service:
                monitored_services['services'][service.name] = [service.plugin_name, service.interval]
            else:
                monitored_services['sub_services'][service.name] = []
                # get last point from redis in order to acquire the sub-service-key
                last_data_point_key = "StatusData_%s_%s_latest" % (host_obj.id, service.name)
                last_point_from_redis = REDIS_OBJ.lrange(last_data_point_key, -1, -1)[0]
                if last_point_from_redis:
                    data, data_save_time = json.loads(last_point_from_redis)
                    if data:
                        service_data_dic = data.get('data')
                        for serivce_key, val in service_data_dic.items():
                            monitored_services['sub_services'][service.name].append(serivce_key)

    return render(request, 'host_detail.html', {'host_obj': host_obj, 'monitored_services': monitored_services})


def hosts_status(request):

    hosts_data_serializer = serializer.StatusSerializer(request, REDIS_OBJ)
    hosts_data = hosts_data_serializer.by_hosts()

    return HttpResponse(json.dumps(hosts_data))


def hostgroups_status(request):
    group_serializer = serializer.GroupStatusSerializer(request,REDIS_OBJ)
    group_serializer.get_all_groups_status()

    return HttpResponse('ss')


def graphs_generator(request):

    graphs_generator = graphs.GraphGenerator2(request, REDIS_OBJ)
    graphs_data = graphs_generator.get_host_graph()
    print("graphs_data", graphs_data)
    return HttpResponse(json.dumps(graphs_data))


def graph_bak(request):

    # host_id = request.GET.get('host_id')
    # service_key = request.GET.get('service_key')
    # print("graph:", host_id,service_key)

    graph_generator = graphs.GraphGenerator(request, REDIS_OBJ)
    graph_data = graph_generator.get_graph_data()
    if graph_data:
        return HttpResponse(json.dumps(graph_data))


def trigger_list(request):
    host_id = request.GET.get("by_host_id")
    host_obj = models.Host.objects.get(id=host_id)
    alert_list = host_obj.eventlog_set.all().order_by('-date')
    return render(request, 'monitor/trigger_list.html', locals())


def host_groups(request):
    host_groups = models.HostGroup.objects.all().order_by('id')
    level_1 = 0
    level_2 = 0
    level_3 = 0
    level_4 = 0
    level_5 = 0
    for i in host_groups:
        services_list_obj = models.Template.objects.filter(hostgroup__id=i.id).values('services')
        services_count_list = (len([i for i in services_list_obj]))
        trigger_list_obj = models.EventLog.objects.filter(host__host_groups=i)
        trigger_count_list = (len(trigger_list_obj))
        lastest_time = time.ctime()
        for i in trigger_list_obj:
            if i.trigger.severity == 1:
                level_1 += 1
            elif i.trigger.severity == 2:
                level_2 += 1
            elif i.trigger.severity == 3:
                level_3 += 1
            elif i.trigger.severity == 4:
                level_4 += 1
            elif i.trigger.severity == 5:
                level_5 += 1
    return render(request, 'monitor/host_groups.html', locals())


@csrf_exempt
def client_data_sysinfo(request):
    host_sysinfo_key = "HostSystemInfo_%s" % request.POST.get('client_id')
    REDIS_OBJ.set(host_sysinfo_key, request.POST.get('data'))
    return HttpResponse(json.dumps("{'success':1,'data':'recv sysinfo success'}"))


def this_host_detail(request):
    host_id = request.GET.get("by_host_id")
    host_sysinfo_key = "HostSystemInfo_%s" % host_id
    sysinfo_obj = json.loads(REDIS_OBJ.get(host_sysinfo_key))
    return render(request, 'monitor/this_host_detail.html', locals())


