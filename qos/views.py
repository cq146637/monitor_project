from django.shortcuts import render, HttpResponse

# Create your views here.
from qos.data_handler import DataProcess
from qos.backends import redis_conn
from untitled import settings
from qos.backends import ip_lookup
REDIS_OBJ = redis_conn.redis_conn(settings)
GLOBAL_REALTIME_WATCHING_QUEUES = {}
IP_DB_DATA = ip_lookup.IPLookup(ip_db_filename=settings.IP_DB_FILE).ip_db_data


def data_report(request):
    print(request.POST)
    data_process_obj = DataProcess(request, REDIS_OBJ, GLOBAL_REALTIME_WATCHING_QUEUES, IP_DB_DATA)
    if data_process_obj.is_valid():
        data_process_obj.save()

    else:
        print("invalid data:")
        pass  # invalid data
    msg = 'jsonpcallback({"Email":"alex@126.com","Remark":"我来自服务器端哈哈"})'
    return HttpResponse(msg)

