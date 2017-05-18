# -*- coding: utf-8 -*-
from saltapi import SaltAPI
import threading
import ConfigParser
asset_info = []


def get_server_asset_info(tgt,url,user,passwd,device):
    '''
    Salt API得到资产信息，进行格式化输出
    '''
    asset_info=[]
    cf = ConfigParser.ConfigParser()
    cf.read("config.ini")
    info = []
    sapi = SaltAPI(url=url,username=user,password=passwd)
    ret = sapi.remote_noarg_execution(tgt,'grains.items')
    ret2 = sapi.remote_noarg_execution(tgt,'status.diskusage')
    disk=(ret2['/']['total']/(1000*1000))/1000.0
    manufacturer = ret['manufacturer']
    info.append(manufacturer)
    productname = ret['productname']
    info.append(productname)
    serialnumber = ret['serialnumber']
    info.append(serialnumber)
    cpu_model = ret['cpu_model']
    info.append(cpu_model)
    num_cpus = int(ret['num_cpus'])
    info.append(num_cpus)
    num_gpus = int(ret['num_gpus'])
    info.append(num_gpus)
    mem_total = ret['mem_total']
    info.append(mem_total)
    info.append(disk)
    id = ret['id']
    info.append(id)
    lan_ip = ret['ip4_interfaces'][device]
    info.append(lan_ip)
    sys_ver = ret['os'] + ret['osrelease'] + '-' + ret['osarch']
    info.append(sys_ver)
    asset_info.append(info)
    return asset_info
if __name__ == '__main__':
    print get_server_asset_info('u1','https://10.0.1.148:8888','xiaoluo','123456','eth0')
