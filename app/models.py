#coding: utf-8
from django.db import models
from django.contrib import admin
# Create your models here.
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import *
import time
class Idc(models.Model):
    idc_name = models.CharField(max_length=40, verbose_name=u'机房名称')
    networr_bandwidth=models.CharField(max_length=50,verbose_name=u'网络带宽')
    operator=models.CharField(max_length=50,verbose_name=u'运营商')
    room_type=models.CharField(max_length=50,verbose_name=u'机房类型')
    Contact_person=models.CharField(max_length=50,verbose_name=u'联系人')
    phone = models.CharField(max_length=32, verbose_name=u'联系电话')
    address = models.CharField(max_length=128, blank=True, null=True, verbose_name=u"机房地址")
    create_time = models.DateField(auto_now=True)
    remark = models.CharField(max_length=200,blank=True, null=True,verbose_name=u'备注')

    def __unicode__(self):
	return self.idc_name
    class Meta:
	verbose_name = u'机房列表'
        verbose_name_plural = u'机房列表'

class Login_Record(models.Model):
    name = models.CharField(max_length=40, verbose_name=u'登录用户')
    loginTime = models.DateTimeField(auto_now=True, verbose_name=u'登录时间')
    ip = models.IPAddressField(unique=False,verbose_name=u'登录IP地址')
    status = models.IntegerField(default=0,verbose_name=u'是否成功')
    def __unicode__(self):
        return self.name
    class Meta:
        verbose_name=u'登录用户'
        verbose_name_plural=u'登录用户'

class HostList(models.Model):
    ip = models.IPAddressField(unique=True, verbose_name=u'IP外网地址')
    ip_lan = models.IPAddressField(unique=True, verbose_name=u'IP内网地址')
    hostname = models.CharField(max_length=30, verbose_name=u'主机名')
    fast_server_code=models.CharField(max_length=200, verbose_name=u'快速服务码')
    host_type = models.CharField(max_length=200, verbose_name=u'服务器型号')
    jiekou_status=models.CharField(max_length=200, verbose_name=u'接口状态')
    os_type= models.CharField(max_length=200, verbose_name=u'操作系统')
    zicai_code= models.CharField(max_length=200, verbose_name=u'资材编号')
    group = models.ManyToManyField('Group', null=True, blank=True ,verbose_name=u'组名')
    application = models.CharField(max_length=20, verbose_name=u'应用')
    bianhao = models.CharField(max_length=30, verbose_name=u'编号')
    idc_name = models.CharField(max_length=40,null=True,blank=True, verbose_name=u'所属机房')
    def __unicode__(self):
        return self.ip
    class Meta:
        verbose_name = u'主机列表'
	verbose_name_plural = u'主机列表'


class  net_dev(models.Model):
    brand=models.CharField(max_length=200,verbose_name=u'品牌')
    model_num=models.CharField(max_length=100,verbose_name=u'型号')
    type=models.CharField(max_length=100,verbose_name=u'类型')
    addr=models.CharField(max_length=200,verbose_name=u'设备位置')
    idc_name = models.CharField(max_length=40, null=True, blank=True, verbose_name=u'所属机房')
    group = models.ManyToManyField('Group', null=True, blank=True, verbose_name=u'组名')
class ServerAsset(models.Model):
    manufacturer = models.CharField(max_length=20, verbose_name=u'厂商')
    productname = models.CharField(max_length=30, verbose_name=u'产品型号')
    service_tag = models.CharField(max_length=80, verbose_name=u'序列号')
    cpu_model = models.CharField(max_length=50, verbose_name=u'CPU型号')
    cpu_nums = models.PositiveSmallIntegerField(verbose_name=u'CPU线程数')
    cpu_groups = models.PositiveSmallIntegerField(verbose_name=u'CPU物理核数')
    mem = models.CharField(max_length=100, verbose_name='内存大小')
    disk = models.CharField(max_length=300, verbose_name='硬盘大小')
    hostname = models.CharField(max_length=30, verbose_name=u'主机名')
    ip = models.CharField(max_length=20, unique=True,verbose_name=u'IP地址')
    os = models.CharField(max_length=20, verbose_name=u'操作系统')
    def __unicode__(self):
        return u'%s - %s' %(self.ip, self.hostname )

    class Meta:
        verbose_name = u'主机资产信息'
        verbose_name_plural = u'主机资产信息管理'

class Group(models.Model):
    name = models.CharField(max_length=50,unique=True)
    def __unicode__(self):
        return self.name
    class Meta:
        verbose_name = u'主机组信息'
        verbose_name_plural = u'主机组信息管理'
class Upload(models.Model):
    headImg = models.FileField(upload_to = '/web/CMDB/upload')
    def __unicode__(self):
        return self.headImg
    class Meta:
	verbose_name = u'文件上传'
        verbose_name_plural = u'文件上传'
class File_Record(models.Model):
    hostname = models.CharField(max_length=30, verbose_name=u'主机名')
    name = models.CharField(max_length=40, verbose_name=u'操作用户')
    filename = models.CharField(max_length=300, verbose_name=u'文件名')
    ip = models.IPAddressField(verbose_name=u'IP地址')
    start_time = models.DateTimeField(auto_now=True, verbose_name=u'操作时间')
    file_type = models.CharField(max_length=20)
    def __unicode__(self):
        return self.name
    class Meta:
        verbose_name=u'主机名'
        verbose_name=u'操作用户'
class cmd_run(models.Model):
    ip = models.IPAddressField(verbose_name=u'IP地址')
    command = models.CharField(max_length=30, verbose_name=u'命令')
    track_mark = models.IntegerField()
    def __unicode__(self):
	       return self.ip
    class Meta:
        verbose_name = u'命令管理'
        verbose_name_plural = u'命令管理'
class cmd_record(models.Model):
    hostname = models.CharField(max_length=30, verbose_name=u'主机名')
    name = models.CharField(max_length=40, verbose_name=u'操作用户')
    ip = models.IPAddressField(verbose_name=u'IP地址')
    cmd = models.CharField(max_length=100)
    start_time = models.DateTimeField(auto_now=True, verbose_name=u'操作时间')
    def __unicode__(self):
        return self.cmd
    class Meta:
        verbose_name=u'主机名'
        verbose_name=u'操作用户'
class salt_return(models.Model):
   fun = models.CharField(max_length=50)
   jid = models.CharField(max_length=255)
   result = models.TextField()
   host = models.CharField(max_length=255)
   success = models.CharField(max_length=10)
   full_ret = models.TextField()
   def __unicode__(self):
        return self.host
   class Meta:
        verbose_name = u'命令返回结果'
        verbose_name_plural = u'命令返回结果'
