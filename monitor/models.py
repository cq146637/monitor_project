# -*- coding: utf-8 -*-
__author__ = 'CQ'

from django.db import models

# Create your models here.


class Host(models.Model):
    """
        被监控主机
    """
    name = models.CharField(max_length=64, unique=True)
    ip_addr = models.GenericIPAddressField(unique=True)
    host_groups = models.ManyToManyField('HostGroup', blank=True)
    templates = models.ManyToManyField('Template', blank=True)
    monitored_by_choies = (
        ('agent', 'Agent'),
        ('snmp', 'SNMP'),
        ('wget', 'WGET')
    )
    monitored_by = models.CharField('监控方式', max_length=64, choices=monitored_by_choies, default=1)
    status_choices = (
        (1, 'Online'),
        (2, 'Down'),
        (3, 'Unreachable'),
        (4, 'Offline'),
        (5, 'Problem'),
    )
    host_alive_interval = models.IntegerField('主机存活状态检测间隔', default=10)
    status = models.IntegerField('状态', choices=status_choices, default=1)
    memo = models.TextField('备注', max_length=128, blank=True, null=True)

    def __str__(self):
        return self.name


class HostGroup(models.Model):
    """
        主机组，相同的监控参数
    """
    name = models.CharField(max_length=64, unique=True)
    templates = models.ManyToManyField('Template', blank=True)
    memo = models.TextField('备注', max_length=128, blank=True, null=True)

    def __str__(self):
        return self.name


class Template(models.Model):
    """
        一批主机的监控配置文件
        服务组合
        触发器组合
        修改triggers就可以实现对一批机器共同修改
    """
    name = models.CharField('模板名称', max_length=64, unique=True)
    services = models.ManyToManyField('Service', verbose_name="服务列表")
    triggers = models.ManyToManyField('Trigger', verbose_name="触发器列表", blank=True)
    # template_self = models.ForeignKey('self', to_field='id', on_delete='SET_NULL', verbose_name='关联模板列表', blank=True)

    def __str__(self):
        return self.name


class Service(models.Model):
    """
            对象：cpu, ram, disk, ...
            PS：应用名称格式一定要正确GetAppMySQLStatus
    """
    name = models.CharField('服务名称', max_length=64, unique=True)
    interval = models.IntegerField('监控间隔', default=60)
    plugin_name = models.CharField('插件名', max_length=64, default='n/a')
    items = models.ManyToManyField('ServiceItems', verbose_name='指标列表', blank=True)
    has_sub_service = models.BooleanField(default=False, help_text='如果一个服务器还有独立子服务，选择这个，例如：网卡服务有多个独立的子网卡')
    memo = models.CharField('备注', max_length=128, blank=True, null=True)

    def __str__(self):
        return self.name


class ServiceItems(models.Model):
    """
        对象：idle, system, users, ...
        name = linux idle
        key = idle
    """
    name = models.CharField(max_length=64)
    key = models.CharField(max_length=64)
    data_type_choices = (
        ('int', "int"),
        ('float', "float"),
        ('str', "string"),
    )
    data_type = models.CharField('指标数据类型', max_length=32, choices=data_type_choices, default=1)
    memo = models.CharField('备注', max_length=128, blank=True, null=True)

    def __str__(self):
        return self.name


class Trigger(models.Model):
    """
        某监控值超过定义好的阈值，触发定义检测函数，检测是否达到报警级别
    """
    name = models.CharField('触发器名称', max_length=64)
    severity_choices = (
        (1, "Not Classified"),
        (2, "Information"),
        (3, "Warning"),
        (4, "Average"),
        (5, "High"),
        (6, "Disaster"),
    )
    # expressions = models.ManyToManyField('TriggerExpression', verbose_name=u"条件表达式")
    severity = models.IntegerField('报警级别', choices=severity_choices)
    enabled = models.BooleanField(default=True)
    memo = models.TextField("备注", blank=True, null=True)

    def __str__(self):
        return "<service:%s, severity:%s>" % (self.name, self.severity)


class TriggerExpression(models.Model):
    """
        处理实际的触发函数，一个条件对应一个触发器
        多条件关联时，只需要trigger和service就能判断是否关联
        然后再使用logic_type确定关联关系
    """
    trigger = models.ForeignKey('Trigger', on_delete=models.CASCADE, verbose_name='所属触发器')
    service = models.ForeignKey('Service', on_delete=models.CASCADE, verbose_name="关联服务")
    service_items = models.ForeignKey('ServiceItems', on_delete=models.CASCADE, verbose_name="关联服务指标")
    specified_item_key = models.CharField(verbose_name="只监控指定的指标", max_length=64, blank=True, null=True)
    operator_type_choices = (
        ('eq', '='),
        ('lt', '<'),
        ('gt', '>')
    )
    operator_type = models.CharField("运算符", max_length=16, choices=operator_type_choices)
    operator_calc_type_choices = (
        ('avg', "Average"),
        ('max', "Max"),
        ('hit', "Hit"),
        ('last', "Last"),
    )
    data_calc_func = models.CharField(u"数据处理方式", choices=operator_calc_type_choices, max_length=64, default=1)
    operator_calc_args = models.CharField("函数传入参数", help_text=u"若是多个参数,则用逗号分开,第一个值是时间", max_length=64)
    threshold = models.IntegerField(u"阈值")
    logic_type_choices = (
        ('or', "OR"),
        ('and', "AND"),
    )
    logic_type = models.CharField("多条件关联关系", choices=logic_type_choices, max_length=32, blank=True, null=True)

    def __str__(self):
        return "%s %s(%s(%s))" % (self.service_items, self.operator_type, self.data_calc_func, self.operator_calc_args)

    class Meta:
        pass   # unique_together = ('trigger_id','service')


class Action(models.Model):
    name = models.CharField(max_length=64, unique=True)
    host_groups = models.ManyToManyField('HostGroup', blank=True)
    hosts = models.ManyToManyField('Host', blank=True)
    triggers = models.ManyToManyField('Trigger', blank=True, help_text="关联触发器")
    interval = models.IntegerField('报警间隔', default=300)
    operations = models.ManyToManyField('ActionOperation')
    recover_notice = models.BooleanField("故障恢复后发送通知消息", default=True)
    recover_subject = models.CharField(max_length=128, blank=True, null=True)
    recover_message = models.TextField(blank=True, null=True)
    enabled = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ActionOperation(models.Model):
    """
        具体动作在这里定义
        报警升级判断：
            1. 前5次发邮件，6次到10次发短信，
    """
    name = models.CharField(max_length=64)
    step = models.SmallIntegerField("第几次报警", default=1)
    action_type_choices = (
        ('email', "Email"),
        ('sms', "SMS"),
        ('script', "script"),
    )
    action_type = models.CharField("动作类型", choices=action_type_choices, default='email', max_length=64)
    notifiers = models.ManyToManyField("UserProfile", verbose_name="通知对象", blank=True)
    _msg_format = '''Host({hostname},{ip}) service({service_name}) has issue at ({time}),msg:{msg}'''
    msg_format = models.CharField("消息格式", max_length=128, default=_msg_format)

    def __str__(self):
        return self.name


class Maintenance(models.Model):
    name = models.CharField(max_length=64, unique=True)
    hosts = models.ManyToManyField('Host', blank=True)
    host_groups = models.ManyToManyField("HostGroup", blank=True)
    content = models.TextField("维护内容")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True
    )
    name = models.CharField(max_length=64, unique=True)
    gender = models.CharField(max_length=16, null=False)
    department = models.CharField(max_length=64, null=False)
    position = models.CharField(max_length=64, null=False)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    token = models.CharField(max_length=128, blank=True, null=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    user_permissions = True
    groups = None

    def __str__(self):
        return self.name


class EventLog(models.Model):
    """存储报警及其它事件日志"""
    event_type_choices = ((0, '报警事件'), (1, '维护事件'))
    event_type = models.SmallIntegerField(choices=event_type_choices, default=0)
    host = models.ForeignKey("Host", on_delete=models.CASCADE)
    trigger = models.ForeignKey("Trigger", blank=True, null=True, on_delete=models.CASCADE)
    log = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)


