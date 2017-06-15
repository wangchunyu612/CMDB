#coding=utf-8
# Create your views here.
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response,render
from django.template import Template,loader,RequestContext
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import auth
from django import  forms
from django.db.models import Q
from app.models import *
from app.backend.saltapi  import SaltAPI
from app.backend.asset_info import get_server_asset_info
import MySQLdb as mysql,datetime
import  ConfigParser,sys,json,os,time,pickle
#import salt.client
import logging
from app.page import  pages
from django.db.models import Q
import csv
from  new_api import  *
#db = mysql.connect(user="root", passwd="123456", db="monitor", charset="utf8")
#db.autocommit(True)
#c = db.cursor()

#client=salt.client.LocalClient()

timeformat1 = '%Y-%m-%d %H:%M:%S'
logPath = '/var/log/app/'
if not os.path.exists(logPath):
    os.makedirs(logPath)
if not(logPath[-1] == '/'): logPath = logPath + '/'
loggingFile = logPath + 'AppServer' + time.strftime('%Y-%m-%d', time.localtime()) + '.log'
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
shdlr = logging.StreamHandler()
shdlr.setLevel(logging.WARNING)
shdlr.setFormatter(formatter)
fhdlr = logging.FileHandler( loggingFile )
fhdlr.setLevel(logging.INFO)
fhdlr.setFormatter(formatter)
logger.addHandler(shdlr)
logger.addHandler(fhdlr)
print time.asctime() + ' - INFO: AppServer started'

def saltstack():
    config = ConfigParser.ConfigParser()
    config.read("/web/CMDB/app/backend/config.ini")
    url = config.get("saltstack","url")
    user = config.get("saltstack","user")
    passwd = config.get("saltstack","pass")
    device = config.get("network","device")
    result_api={'url':url,'user':user,'passwd':passwd,'device':device}
    return result_api
def wirte_track_mark(num):
    f = open("/web/CMDB/app/backend/track_num.conf",'w')
    try:
        f.write(num)
    finally:
        f.close()
    return "ok"
def read_track_mark():
    f = open("/web/CMDB/app/backend/track_num.conf")
    try:
	num = f.read()
    finally:
	f.close()
    return num
def date_result(data):
    timeArray = time.strptime(data, "%Y-%m-%d %H:%M:%S")
    timeStamp = int(time.mktime(timeArray)) - 50400
    return timeStamp

@login_required
def index(request):
    total_idc =Idc.objects.aggregate(Count('idc_name')) #获取idc机房的数量的对象
    idc_num = total_idc["idc_name__count"]  #获得idc机房的数量
    total_host = HostList.objects.aggregate(Count('hostname'))  #获得主机的对象
    host_num = total_host["hostname__count"] #获得主机数量
    login_user = request.user
    userinfo = User.objects.get(username=request.user)
    login_info = Login_Record.objects.filter(status=1).filter(name=request.user).order_by("-loginTime")[0:6]
    return render_to_response("index.html",locals())
#获取主机的IP地址
def get_clinet_ip(request):
    try:
        real_ip = request.MEAT['HTTP_X_FORWARDED_FOR']
        regip = real_ip.split(",")[0]
    except:
        regip = request.META['REMOTE_ADDR']
    return regip
def logout(request):
    session_key = request.session.session_key
    auth.logout(request)
    return render_to_response("login.html")
def login(request):
    return render_to_response("login.html")
def authin(request):
    username = request.POST.get('username','') #从提交的HTML页面获取username
    password = request.POST.get('password','') #从提交的HTML页面获取passwrod
    real_ip = get_clinet_ip(request)          #获取到主机的IP地址
    logger.info(username +' - '+ real_ip + ' - connect server' )  #将登陆信息写入日志
    if username and password is not  None:
        try:
             userinfo = User.objects.get(username=username) #用djangop自己的认证用户
        except Exception,e:
             P = Login_Record(name=username, ip=real_ip)
             P.save()
             logger.error(username + ' - ' + real_ip + ' - login failed')
             return render_to_response('login.html', {'login_err': 'Wrong username or password!'})

        user = auth.authenticate(username=username,password=password)
        if userinfo.is_active:
            if user is not None:
                auth.login(request,user)
                P = Login_Record(name=username,ip=real_ip,status=1)
                P.save()
                total_idc =Idc.objects.aggregate(Count('idc_name'))   #aggregate进行聚合统计可以统计平均值 Avg，Count，Max，Min，Sum
                #返回字典
                idc_num = total_idc["idc_name__count"]
                total_host = HostList.objects.aggregate(Count('hostname'))
                host_num = total_host["hostname__count"]
                login_user = username
                login_info = Login_Record.objects.filter(status=1).filter(name=request.user).order_by("-loginTime")[0:6]
                logger.info(username +' - '+ real_ip + ' - login server' )
                return  render_to_response('index.html',locals())  #Python的locals()函数会以dict类型返回当前位置的全部局部变量。
            else:
                P = Login_Record(name=username,ip=real_ip)
                P.save()
                logger.error(username +' - '+ real_ip + ' - login failed' )
                return render_to_response('login.html',{'login_err':'Wrong username or password!'})
        else:
            P = Login_Record(name=username,ip=real_ip)
            P.save()
            logger.error(username +' - '+ real_ip + ' - user is forbbiden' )
            return render_to_response('login.html',{'login_err':'user is forbbiden!'})
    else:
        P = Login_Record(name=username,ip=real_ip)
        P.save()
        logger.error(username +' - '+ real_ip + ' - login failed' )
        return render_to_response('login.html',{'login_err':'Please input username or password!'})
@login_required
def idc(request):
    all_idc = Idc.objects.all()
    return render_to_response("idc.html",locals()) #Python的locals()函数会以dict类型返回当前位置的全部局部变量。

@login_required
def addidc1(request):
    return   render_to_response('idc_add.html',locals())
def addidc2(request):
    nameInput = request.GET['nameInput']
    daikuanInput = request.GET['daikuan']
    yunyingshangInput = request.GET['yunyingshang']
    typeInput = request.GET['type']
    connectInput = request.GET['connect']
    phoneInput = request.GET['phone']
    addressInput = request.GET['address']
    msgInput = request.GET['msgInput']
    all_idc = Idc.objects.all()
    idc_name_list = []
    for i in all_idc:
        idc_name_list.append(i.idc_name)
        #    print idc_name_list
    if nameInput in idc_name_list:
        # logger.error(str(request.user) + ' - ' +'idc name'+' '+str(nameInput) +' - '+'exists!')
        return HttpResponse('exist')
    else:
        idc_add = Idc(idc_name=nameInput, remark=msgInput, networr_bandwidth=daikuanInput, operator=yunyingshangInput,
                      room_type=typeInput, Contact_person=connectInput, phone=phoneInput, address=addressInput)
        idc_add.save()
        # logger.info(str(request.user) + '- '+'add idc name '+ nameInput+'success')
        return HttpResponse('ok')


@login_required
def addidc(request):
    nameInput = request.GET['nameInput']
    daikuanInput = request.GET['daikuan']
    yunyingshangInput = request.GET['yunyingshang']
    typeInput = request.GET['type']
    connectInput = request.GET['connect']
    phoneInput = request.GET['phone']
    addressInput = request.GET['address']
    msgInput = request.GET['msgInput']
    all_idc = Idc.objects.all()
    idc_name_list=[]
    for i in all_idc:
        idc_name_list.append(i.idc_name)
#    print idc_name_list
    if nameInput in idc_name_list:
       # logger.error(str(request.user) + ' - ' +'idc name'+' '+str(nameInput) +' - '+'exists!')
        return HttpResponse('exist')
    else:
        idc_add = Idc(idc_name=nameInput,remark=msgInput,networr_bandwidth=daikuanInput,operator=yunyingshangInput,room_type=typeInput,Contact_person=connectInput,phone=phoneInput,address=addressInput)
        idc_add.save()
        #logger.info(str(request.user) + '- '+'add idc name '+ nameInput+'success')
        return HttpResponse('ok')

@login_required
def idc_delete(request,id=None):
    if request.method == 'GET':
        id = request.GET.get('id')
        idc =Idc.objects.get(id=id)
        Idc.objects.filter(id=id).delete()
        #logger.error(str(request.user)+ ' - '+'delete idc name '+idc.idc_name)
        return HttpResponseRedirect('/idc/')
@login_required
def idc_update(request):
    if request.method == 'POST':
        remark=request.POST.get('msgInput')
        name=request.POST.get('id')
        a=Idc.objects.get(idc_name=name)
        a.remark=remark
        a.save()
        #logger.info(str(request.user)+' - '+'update idc remark '+remark)
        return HttpResponseRedirect('/idc/')
@login_required
def   idc_edit(request):
    if request.method == 'GET':
        id = request.GET.get('id')
        all_idc = Idc.objects.filter(id=id)
        return render_to_response("idc_edit.html", locals())
def idcresult(request):
    if  request.method =='GET':
        print  request.GET
        id = int(request.GET['id'])
        #id = request.GET.get('id')
        nameInput = request.GET['nameInput']
        daikuanInput = request.GET['daikuan']
        yunyingshangInput = request.GET['yunyingshang']
        typeInput = request.GET['type']
        connectInput = request.GET['connect']
        phoneInput = request.GET['phone']
        addressInput = request.GET['address']
        msgInput = request.GET['msgInput']
        try:
            idc_update=Idc.objects.filter(id=id).update(idc_name=nameInput,remark=msgInput,networr_bandwidth=daikuanInput,operator=yunyingshangInput,room_type=typeInput,Contact_person=connectInput,phone=phoneInput,address=addressInput)
        except Exception,e:
            return HttpResponseRedirect('/idc/')
        finally:
            return HttpResponse('ok')


@login_required
def netdev(request):
    all_net_dev = net_dev.objects.all()
    all_idc = Idc.objects.all()
    net_dev_count = net_dev.objects.all().count()
    print    net_dev_count
    return    render_to_response('net_dev.html',locals())
@login_required
def net_add_dev(request):
    #if  request.method =='GET':
        print     request.GET
        print  request.POST.get('brand1')
        brand=request.GET['brand']
        model_num=request.GET['model_num']
        type=request.GET['type']
        addr=request.GET['addr']
        idc_name=request.GET['idc_name']
        net_add=net_dev(brand=brand,model_num=model_num,type=type,addr=addr,idc_name=idc_name)
        net_add.save()
        return  HttpResponse('ok')

@login_required
def net_delete(request):
    if request.method == 'GET':
        id = request.GET.get('id')
        NetInfo = net_dev.objects.get(id=id)
        net_dev.objects.filter(id=id).delete()
        #logger.error(str(request.user) + ' - ' + 'delmac' + ' - hostname:' + HostInfo.hostname + '- host_ip:' + HostInfo.ip + '- idc_name:' + HostInfo.idc_name + '- host_application:' + HostInfo.application + '- host_bianhao:' + HostInfo.bianhao)
        return HttpResponseRedirect('/net_dev/')
@login_required
def net_edit(request):
    if request.method == 'GET':
        id = request.GET.get('id')
        print id
        all_idc = Idc.objects.all()
        all_net_dev = net_dev.objects.filter(id=id)
        return render_to_response("net_edit.html",locals())
@login_required
def netresult(request):
    if request.method =='GET':
        id = int(request.GET['id'])
        print  id
        brand = request.GET['brand']
        model_num = request.GET['model_num']
        type = request.GET['type']
        addr = request.GET['addr']
        idc_name = request.GET['idc_name']
    try:
        net_update = net_dev.objects.filter(id=id).update(brand=brand,model_num=model_num,type=type,addr=addr,idc_name=idc_name)
        print   mac_update
        #mac_update.save()
        #logger.info(str(request.user) + ' - '+'editmac'+ ' - hostname:' +  name+'- host_ip:' +  ip+'- idc_name:' + idc_name+'- application:' + service+'- bianhao:' +idc_bh)
        return HttpResponse('ok')
    finally:
        return HttpResponse('ok')



@login_required
def  net_search(request):
    if request.method =='POST':
         all_idc = Idc.objects.all()
         search_word=request.POST.get('keyword')
         print    search_word
         if search_word =='':
            return  HttpResponseRedirect('/net_dev/')
         else:
            all_net_dev = net_dev.objects.filter(Q(brand=search_word) |
                                         Q(model_num=search_word) |
                                         Q(type=search_word) |
                                         Q(addr=search_word) |
                                         Q(idc_name=search_word))
            net_dev_count = all_net_dev.count()
            all_idc = Idc.objects.all()
            return render_to_response('net_dev.html', locals())
    else:
        return HttpResponseRedirect('/net_dev/')

@login_required
def  domain_name(request):
     all_domain = domain.objects.all()
     domain_count = all_domain.count()
     return  render_to_response('domain.html',locals())
@login_required
def   adddomain(request):
    if   request.method == 'GET':
          print     request.GET
          name = request.GET['name']
          project = request.GET['project']
          status = request.GET['status']
          register_time = request.GET['register_time']
          expire_date = request.GET['expire_date']
          remark =  request.GET['remark']
    all_domain = domain.objects.all()
    domain_count = all_domain.count()
    all_domain_list=[]
    for   domain_name  in all_domain:
           all_domain_list.append(domain_name.domain_name)
    if    name  in  all_domain_list:
          return    HttpResponseRedirect('/domain/')
    else:
          domain_add=domain(domain_name=name,project=project,status=status,register_time=register_time,expire_date=expire_date,remark=remark)
          domain_add.save()
          return HttpResponse('ok')

@login_required
def deldomain(request):
       id=int(request.GET['id'])
       all_domain = domain.objects.all()
       domain_count = all_domain.count()
       del_domain = domain.objects.filter(id=id).delete()
       return HttpResponseRedirect('/domain/')
@login_required
def domain_edit(request):
    if request.method == 'GET':
        id = request.GET.get('id')
        #all_domain = domain.objects.all()
        all_domain = domain.objects.filter(id=id)
        return render_to_response("domain_edit.html",locals())


def domain_result(request):
    if request.method == 'GET':
            print   request.GET
            id = int(request.GET['id'])
            name = request.GET['name']
            project = request.GET['project']
            status = request.GET['status']
            register_time = request.GET['register_time']
            expire_date = request.GET['expire_date']
            remark = request.GET['remark']
    try:
        domain_update=domain.objects.filter(id=id).update(domain_name=name,project=project,status=status,register_time=register_time,expire_date=expire_date,remark=remark)
        return HttpResponse('ok')
    finally:
        return HttpResponse('ok')
@login_required
def mac(request):
    all_host = HostList.objects.all().order_by("ip")
    all_idc = Idc.objects.all()
    net_mac_count = all_host.count()
    contact_list, p, contacts, page_range, current_page, show_first, show_end = pages(all_host, request)
    return render_to_response("mac.html",locals(),context_instance=RequestContext(request))
@login_required
def addmac(request):
    if request.method == 'GET':
        name = request.GET['name']
        ip = request.GET['ip']
        ip_lan = request.GET['ip_lan']
        servicecode = request.GET['servicecode']
        machine_type = request.GET['machine_type']

        os_type = request.GET['os_type']
        zicai_code = request.GET['zicai_code']
        idc_name = request.GET['idc_name']
        service = request.GET['service']
        idc_bh = request.GET['idc_jg']
        mac_add = HostList(ip=ip,hostname=name,application=service,idc_name=idc_name,bianhao=idc_bh,ip_lan=ip_lan,fast_server_code=servicecode,host_type=machine_type,os_type=os_type,zicai_code=zicai_code)
        mac_add.save()
        logger.info(str(request.user)+' - '+'addmac'+ ' - '+name+'-'+str(ip)+'-'+idc_name+'-'+service+'-'+idc_bh)
        return HttpResponse('ok')
@login_required
def check_host(request):
    if request.method == 'GET':
        idc_name = request.GET['idc_name']
        all_host = HostList.objects.filter(idc_name=idc_name)
        net_mac_count=all_host.count()
        print idc_name
        return render_to_response("mac.html",locals())
@login_required
def mac_delete(request,id=None):
    if request.method == 'GET':
        id = request.GET.get('id')
        HostInfo = HostList.objects.get(id=id)
        HostList.objects.filter(id=id).delete()
        logger.error(str(request.user)+' - '+'delmac'+ ' - hostname:'+HostInfo.hostname+'- host_ip:'+HostInfo.ip+'- idc_name:'+HostInfo.idc_name+'- host_application:'+HostInfo.application+'- host_bianhao:'+HostInfo.bianhao)
        return HttpResponseRedirect('/mac/')
@login_required
def mac_edit(request,id=None):
    if request.method == 'GET':
        id = request.GET.get('id')
        all_idc = Idc.objects.all()
        all_host = HostList.objects.filter(id=id)
        return render_to_response("mac_edit.html",locals())
@login_required
def macresult(request):
    if request.method =='GET':
        id = int(request.GET['id'])
        ip = request.GET['ip']
        ip_q=request.POST.get('ip_q')
        print   ip_q
        name=request.GET['name']
        ip_lan = request.GET['ip_lan']
        servicecode = request.GET['servicecode']
        machine_type = request.GET['machine_type']
        #api_status = request.GET['api_status']
        os_type = request.GET['os_type']
        zicai_code = request.GET['zicai_code']
        idc_name = request.GET['idc_name']
        service = request.GET['service']
        idc_bh = request.GET['idc_jg']
    try:
        mac_update = HostList.objects.filter(id=id).update(ip=ip,hostname=name,application=service,idc_name=idc_name,bianhao=idc_bh,ip_lan=ip_lan,fast_server_code=servicecode,host_type=machine_type,os_type=os_type,zicai_code=zicai_code)
        print   mac_update
        #mac_update.save()
        logger.info(str(request.user) + ' - '+'editmac'+ ' - hostname:' +  name+'- host_ip:' +  ip+'- idc_name:' + idc_name+'- application:' + service+'- bianhao:' +idc_bh)
        return HttpResponse('ok')
    finally:
        return HttpResponse('ok')

@login_required
def   mac_search(request):
    print  request.method
    if request.method =='POST':
            all_idc = Idc.objects.all()
            search_word = request.POST.get('keyword')
            print    search_word
            if search_word == '':
                return HttpResponseRedirect('/mac/')
            else:
                all_host = HostList.objects.filter(Q(ip=search_word) |
                                                     Q(hostname=search_word) |
                                                     Q(application=search_word) |
                                                     Q(idc_name=search_word) |
                                                     Q(ip_lan=search_word)|
                                                   Q(fast_server_code=search_word) |
                                                   Q(host_type=search_word) |
                                                   Q(jiekou_status=search_word) |
                                                   Q(os_type=search_word) |
                                                   Q(zicai_code=search_word))
                net_mac_count = all_host.count()
                search=1

                contact_list, p, contacts, page_range, current_page, show_first, show_end = pages(all_host, request)
                return render_to_response('mac.html', locals())
    else:
        return HttpResponseRedirect('/mac/')
@login_required
def download(request):
    if request.method == 'GET':
	all_host = HostList.objects.all()
    return render_to_response('download.html',locals())

@login_required
def download_result(request):
    if request.method =='POST':
        hostname = request.POST.get('hostname')
        if request.POST.get('filename') and request.POST.get('path'):
            filepath = request.POST.get('path') + request.POST.get('filename')
        else:
            filepath = request.POST.get('dir')
        print hostname,filepath
#        cmd='salt %s cp.push %s' %(hostname,filepath)
        #ret=client.cmd(hostname,'cp.push',[filepath])
        print ret
#        ret=os.popen(cmd).readlines()
        if ret[hostname]:
            salt_minior_dir='/var/cache/salt/master/minions/'+str(hostname)+'/files'
            fullpath=salt_minior_dir+filepath
            f=open(fullpath)
            data=f.read()
            filename = fullpath.split('/')[-1]
            response = HttpResponse(data,mimetype='application/octet-stream')
            response['Content-Disposition'] = 'attachment; filename=%s' %filename
            real_ip = get_clinet_ip(request)
            file_record = File_Record(hostname=hostname,name=request.user,filename=filepath,ip=real_ip,file_type='download')
            file_record.save()
            return response
        else:
            all_host = HostList.objects.all()
            ret='File not exist or host connect failed'
            return render_to_response('download.html',locals())


class UploadForm(forms.Form):
    headImg = forms.FileField()
@login_required
def upfile(request):
#    if request.method == 'POST':
    all_host = HostList.objects.all()
    all_file = Upload.objects.all()
    uf = UploadForm(request.POST,request.FILES)
    if uf.is_valid():
        headImg = uf.cleaned_data['headImg']
        user = Upload()
        user.headImg = headImg
        user.save()
    return render_to_response('file.html',locals())
@login_required
def file_result(request):
    hostname = request.GET.get('hostname')
    salt_file = request.GET.get('file')
    filename = salt_file.split('/')[-1]
    print filename
    mini_dest = request.GET.get('dir')
    #ret=client.cmd(hostname,'cp.get_file',['salt:/'+salt_file,mini_dest])
    print ret
    if ret[hostname]:
        if 'exception' in ret[hostname]:
            result = {'mes':'推送目录填写错误'}
            return HttpResponse(json.dumps(result))
        if  mini_dest in ret[hostname]:
            print '上传成功'
            result = {'mes':"推送成功"}
            real_ip= get_clinet_ip(request)
            file_record = File_Record(hostname=hostname,name=request.user,filename=filename,ip=real_ip,file_type='upload')
            file_record.save()
            return HttpResponse(json.dumps(result))
    else:
        print '上传失败'
        mes='上传至主机%s失败' % str(hostname)
        result = {'mes':mes}
        return HttpResponse(json.dumps(result))
@login_required
def del_upload_file(request):
    Upload.objects.all().delete()
    Path='/web/CMDB/upload/'
    if os.path.exists(Path):
        files=os.listdir(Path)
        for i in files:
            os.remove(Path+i)
    return HttpResponse('ok')
@login_required
def groupfile(request):
#    if request.method == 'POST':
    all_group = Group.objects.all()
    all_file = Upload.objects.all()
    uf = UploadForm(request.POST,request.FILES)
    if uf.is_valid():
        headImg = uf.cleaned_data['headImg']
        user = Upload()
        user.headImg = headImg
        user.save()
    return render_to_response('groupfile.html',locals())
#    else:
#        uf = UserForm()
#        return render_to_response('file.html',{'uf':uf})
@login_required
def groupfile_result(request):
    if request.method == 'GET':
	import sys
	reload(sys)
	sys.setdefaultencoding( "utf-8" )
	g_name = request.GET.get('g_name')
	file = request.GET.get('file')
	dir = request.GET.get('dir')
    print g_name,file,dir
    GroupList = Group.objects.all()
    list_coun = []
    project_success = []
    project_fail = []
    salt_return.objects.filter().delete()
    for groupname in GroupList:
            if groupname.name in g_name:
                print "slected group:",groupname.name
                for selected_ip in HostList.objects.filter(group__name = groupname.name):
                    hosts = HostList.objects.filter(ip=selected_ip.ip)
                    for host in hosts:
                        key_id = host.hostname
                        cmd = "salt %s cp.get_file salt:/%s %s"  %(key_id,file,dir)
                        ret=client.cmd(key_id,'cp.get_file',['salt:/'+file,dir])
                        print ret
                        if dir in ret[key_id]:
                            print '上传成功'
                            b=salt_return(jid=cmd,host=key_id,success='1',result=ret)
                            b.save()
                            list_coun.append(host)
                        else:
                            b=salt_return(jid=cmd,host=key_id,success='0',result=ret)
                            b.save()
                            print '上传失败'
                            list_coun.append(host)
                num = len(list_coun)
                print num
                wirte_track_mark(str(num))
                all_result = salt_return.objects.all()[0:num]
                for projects in all_result:
                    print projects.success
                    if projects.success == '1':
                        project_success.append(projects.success)
                    else:
                        project_fail.append(projects.success)
                success_num = len(project_success)
                fail_num = len(project_fail)
                result = {'success':success_num,'fail':fail_num}
                return HttpResponse(json.dumps(result))

@login_required
def command(request):
    if request.method == 'GET':
	all_host = HostList.objects.all()
    return render_to_response("command.html",locals())
@login_required
def command_result(request):
    if request.method == 'GET':
        ret_api = saltstack()
        key_id = request.GET.get('hostname')
        command = request.GET.get('command')
        print key_id,command
#        host = HostList.objects.filter(ip=ip)
        sapi = SaltAPI(url=ret_api["url"],username=ret_api["user"],password=ret_api["passwd"])
        try:
            ret = sapi.remote_execution(key_id,'cmd.run',command)
            for i in range(len(ret)):
                ret=ret[i][key_id]
	        r_data = {'host':key_id,'ret':ret}
            data = json.dumps(r_data)
            real_ip = get_clinet_ip(request)
            Cmd_Record = cmd_record(hostname=key_id,name=request.user,ip=real_ip,cmd=command)
            Cmd_Record.save()
            return HttpResponse(data)
        except:
            print '123'
            return HttpResponse('ok')

@login_required
def command_group(request):
    if request.method == 'GET':
	all_group = Group.objects.all()
    return render_to_response("command_group.html",locals())
def command_group_result(request):
    if request.method == 'GET':
	ret_api = saltstack()
        g_name = request.GET.get('g_name')
        command = request.GET.get('command')
        selectIps = []
	list_coun = []
        project_success = []
	project_fail = []
        GroupList = Group.objects.all()
#        salt_return.objects.filter().delete()
        for groupname in GroupList:
            if groupname.name in g_name:
                print "slected group:",groupname.name
                for selected_ip in HostList.objects.filter(group__name = groupname.name):
                    host = HostList.objects.filter(ip=selected_ip.ip)
                    for host in host:
                        key_id = host.hostname
                        sapi = SaltAPI(url=ret_api["url"],username=ret_api["user"],password=ret_api["passwd"])
                        try:
                            ret = sapi.remote_execution(key_id,'cmd.run',command)
		            list_coun.append(host)
                            ret=ret[0][key_id]
                            b=salt_return(jid=command,host=key_id,success='1',result=ret)
                            b.save()
                        except:
                            print "Connect %s failed" % key_id
                            b=salt_return(jid=command,host=key_id,success='0',result='failed')
                            b.save()
		num = len(list_coun)
	        wirte_track_mark(str(num))
		all_result = salt_return.objects.all()[0:num]
		for projects in all_result:
		    project=projects.success
		    if project == '1':
			project_success.append(project)
		    else:
			project_fail.append(project)
		success_num = len(project_success)
		fail_num = len(project_fail)
		result = {'success':success_num,'fail':fail_num}
        return HttpResponse(json.dumps(result))
@login_required
def check_result(request):
    num = int(read_track_mark())
    all_result = salt_return.objects.all().order_by("-id")[0:num]
    return render_to_response("check_result.html",locals())
@login_required
def job(request):
    return render_to_response("job.html")
@login_required
def asset(request):
    all_asset = ServerAsset.objects.all()
    contact_list,p, contacts, page_range, current_page, show_first, show_end=pages(all_asset,request)
    return render_to_response("asset.html",locals())
@login_required
def asset_download(request):
    import codecs
    asset_flag=['manufacturer','productname','service_tag','cpu_model','cpu_nums','cpu_groups','mem','disk','hostname','ip','os']
    down_path_file='/tmp/'+'asset_'+ time.strftime('%Y-%m-%d_%H%M', time.localtime())+'.csv'
    all_asset = ServerAsset.objects.all()
    with open(down_path_file,'wb') as csvfile:
        asset_title=['厂商','产品型号','序列号','主机名','主机ip','操作系统','cpu型号','cpu核数','cpu数','内存大小','硬盘大小']
        csvfile.write(codecs.BOM_UTF8)
        spamwriter = csv.writer(csvfile,dialect='excel')
        spamwriter.writerow(asset_title)
    for asset in all_asset:
            asset_info=[]
            asset_info.append(asset.manufacturer)
            asset_info.append(asset.productname)
            asset_info.append(asset.service_tag)
            asset_info.append(asset.hostname)
            asset_info.append(asset.ip)
            asset_info.append(asset.os)
            asset_info.append(asset.cpu_model)
            asset_info.append(asset.cpu_nums)
            asset_info.append(asset.cpu_groups)
            asset_info.append(asset.mem)
            asset_info.append(asset.disk)
            with open(down_path_file,'a') as csvfile:
                csvfile.write(codecs.BOM_UTF8)
                spamwriter = csv.writer(csvfile,dialect='excel')
                spamwriter.writerow(asset_info)
    f=open(down_path_file)
    data=f.read()
    f.close()
    filename = down_path_file.split('/')[-1]
    response = HttpResponse(data,mimetype='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename=%s' %filename
    return response
@login_required
def asset_auto(request):
    all_host = HostList.objects.all()
    return render_to_response("asset_auto.html",locals())
@login_required
def asset_auto_result(request):
    if request.method == 'GET':
        ret_api = saltstack()
        try:
            client = request.GET.get('client')
            result = get_server_asset_info(client,ret_api["url"],ret_api["user"],ret_api["passwd"],ret_api["device"])
            result_data = ServerAsset()
            result_data.manufacturer = result[0][0]
            result_data.productname = result[0][1]
            result_data.service_tag = result[0][2]
            result_data.cpu_model = result[0][3]
            result_data.cpu_nums = result[0][4]
            result_data.cpu_groups = result[0][5]
            result_data.mem = result[0][6]
            result_data.disk = result[0][7]
            result_data.hostname = result[0][8]
            result_data.ip = result[0][9][0]
            result_data.os = result[0][10]
            result_data.save()
            data = json.dumps(result)
            return HttpResponse(data)
        except Exception,e:
            print str(e)
            print "print check you asset"
            return HttpResponse('ok')
@login_required
def asset_delete(request,id=None):
    if request.method == 'GET':
	id = request.GET.get('id')
        ServerAsset.objects.filter(id=id).delete()
	return HttpResponseRedirect('/asset/')
@login_required
def group(request):
    all_group = Group.objects.all()
    return render_to_response("group.html",locals())
@login_required
def group_result(request):
    if request.method == 'GET':
	group = request.GET.get('g_name')
	data = Group()
	data.name = group
	data.save()
	return HttpResponse("ok")
@login_required
def group_delete(request,id=None):
    id = request.GET['id']
    group_id = Group.objects.get(id=id)
    all_ip=group_id.hostlist_set.all()
    if all_ip:
        return HttpResponse('exist')
    else:
        Group.objects.filter(id=id).delete()
        return HttpResponse('ok')
@login_required
def group_manage(request,id=None):
    if request.method == 'GET':
	id = request.GET.get('id')
	group_name = Group.objects.get(id=id)
 	all_ip = group_name.hostlist_set.all()
	all_host = HostList.objects.all()
    return render_to_response("group_manage.html",locals())
@login_required
def group_manage_delete(request,group_name=None,ip=None):
#    if request.method == 'GET':
#	group_name = request.GET.get('group_name')
#	ip = request.GET.get('ip')
        group_name = request.GET['group_name']
        ip = request.GET['ip']
        try:
	        all_group = Group.objects.filter(name=group_name)
	        all_host = HostList.objects.filter(ip=ip)
	        for group in all_group:
	            group_id= group.id
	        for host in all_host:
	            host_id= host.id
                h = HostList.objects.get(id=host_id)
                g = Group.objects.get(id=group_id)
	        h.group.remove(g)
	        return HttpResponse('ok')
        except:
            return HttpResponse('false')
@login_required
def addgroup_host(request):
    if request.method == 'GET':
	group = request.GET.get('nameInput')
	ip = request.GET.get('hostInput')
	all_group = Group.objects.filter(name=group)
        all_host = HostList.objects.filter(ip=ip)
	for group in all_group:
            group_id= group.id
        try:
            for host in all_host:
                host_id= host.id
            h = HostList.objects.get(id=host.id)
            g = Group.objects.get(id=group_id)
	    h.group.add(g)
	    return HttpResponse('ok')
        except:
            return HttpResponse('false')
@login_required
def oprationfile(request):
    if request.method == 'GET':
        all_host = HostList.objects.all()
        return render_to_response('opration_file.html',locals())
def oprationfile_result(request):
    import shutil
    all_host = HostList.objects.all()
    hostname = request.POST.get('hostInput')
    path = request.POST.get('filepath')
    salt_minior_dir='/var/cache/salt/master/minions/'+str(hostname)+'/files'
    salt_path=salt_minior_dir+path
    print path,hostname
    if os.path.exists(salt_path):
        shutil.rmtree(salt_path)
    client.cmd(hostname,'cp.push_dir',[path])
#    cmd='salt %s cp.push_dir %s' %(hostname,path)
#    ret=os.popen(cmd).readlines()
    if path and '/' in path[-1]:
        files={}
        dirs=os.listdir(salt_path)
        for f in dirs:
            fileList=[]
            filePath=salt_path+f
            if os.path.isfile(filePath):
                '''
                Str_UpdateTime=datetime.datetime.fromtimestamp(os.path.getmtime(filePath))
                FileUpdateTime=Str_UpdateTime.strftime('%Y-%m-%d %H:%M:%S')
                files[f]=FileUpdateTime
                '''
                FileSize=round(os.path.getsize(filePath)/1000.0,1)
                files[f]=FileSize

        print files
        return render_to_response('opration_file.html',locals())
    else:
        mes='*请填写正确的文件路径*'
        return render_to_response('opration_file.html',locals())
@login_required
def oprationfile_check(request):
    hostname=request.GET.get('hostname')
    path=request.GET.get('path')
    filename=request.GET.get('filename')
    print hostname,path,filename
    salt_minior_dir='/var/cache/salt/master/minions/'+str(hostname)+'/files'
    filepath=path+filename
    salt_filepath=salt_minior_dir+path+filename
    print filepath
    f=open(salt_filepath)
    content=f.read()
    f.close()
    print content
    r_data={'hostname':hostname,'filepath':filepath,'content':content}
    data=json.dumps(r_data)
    return HttpResponse(data)
@login_required
def oprationfile_update(request):
    hostname=request.POST.get('hostname')
    filepath=request.POST.get('filepath')
    content=request.POST.get('content')
    content=content.encode("utf-8")
    salt_minior_dir='/var/cache/salt/master/minions/'+str(hostname)+'/files'
    salt_filepath=salt_minior_dir+filepath
    path=os.path.dirname(filepath)+'/'
    f=open(salt_filepath,'w')
    f.write(content)
    f.close()
    client.cmd(hostname,'cp.get_file',['salt:/'+salt_filepath,filepath])
#    cmd='salt %s cp.get_file  salt:/%s %s' % (hostname,salt_filepath,filepath)
#    ret=os.popen(cmd).readlines()
    return render_to_response('opration_update.html',locals())
@login_required
def service_result(request):
    hostname=str(request.GET.get('h'))
    cmd_flag=request.GET.get('cmd')
    all_host = HostList.objects.all()
    print hostname,cmd_flag
    if hostname and cmd_flag:
        if str(cmd_flag)=='1':
            cmd="/root/deploy/deploy.sh -r"
        elif str(cmd_flag)=='2':
            cmd="/root/deploy/deploy.sh -u"
        ret=client.cmd(hostname,'cmd.run',[cmd])
        if ret:
            ret=ret[hostname]
            print ret
            return render_to_response('service_result.html',locals())
        else:
            ret='Connect host  Failed!'
            return render_to_response('service_result.html',locals())
    else:
        return render_to_response('service.html',locals())
@login_required
def user(request):
    all_user = User.objects.all()
    contact_list,p, contacts, page_range, current_page, show_first, show_end=pages(all_user,request)
    return render_to_response("user.html",locals())
@login_required
def adduser(request):
    if request.method == 'GET':
        username = request.GET['username']
        email = request.GET['email']
        password = request.GET['password']
        is_active = request.GET['is_active']
        try:
            userinfo = User.objects.get(username=username)
            return HttpResponse('False')
        except:
            user = User()
            user.username=username
            user.set_password(password)
            user.email=email
            user.is_active = is_active
            user.save()
            return HttpResponse('ok')
@login_required
def user_delete(request,id=None):
    if request.method == 'GET':
        id = request.GET.get('id')
        UserInfo = User.objects.get(username=request.user)
        if UserInfo.is_superuser:
            try:
                UserInfo = User.objects.get(id=id)
                User.objects.filter(id=id).delete()
                logger.error(str(request.user)+' - '+'deluser'+ ' - username:'+str(UserInfo.username))
                return HttpResponse('ok')
            except:
                return HttpResponse('False')
        else:
                return HttpResponse('No')
@login_required
def user_forbidden(request,id=None):
    if request.method == 'GET':
        id = request.GET.get('id')
        UserInfo = User.objects.get(username=request.user)
        if UserInfo.is_superuser:
            try:
                UserInfo = User.objects.get(id=id)
                User.objects.filter(id=id).update(is_active=0)
                logger.info(str(request.user)+' - '+'forbidden_user'+ ' - username:'+str(UserInfo.username))
                return HttpResponse('ok')
            except:
                return HttpResponse('False')
        else:
                return HttpResponse('No')
@login_required
def user_start(request,id=None):
    if request.method == 'GET':
        id = request.GET.get('id')
        UserInfo = User.objects.get(username=request.user)
        if UserInfo.is_superuser:
            try:
                UserInfo = User.objects.get(id=id)
                User.objects.filter(id=id).update(is_active=1)
                logger.info(str(request.user)+' - '+'start_user'+ ' - username:'+str(UserInfo.username))
                return HttpResponse('ok')
            except:
                return HttpResponse('False')
        else:
            return HttpResponse('No')
@login_required
def user_info(request):
    if request.method == 'GET':
        print request.user
        userinfo = User.objects.get(username=request.user)
        return render_to_response("user_info.html",locals())
@login_required
def user_passwd(request):
    if request.method == 'GET':
        userinfo = User.objects.get(username=request.user)
        if userinfo.is_superuser:
            return render_to_response("user_passwd.html")
        else:
            user = request.user
            return render_to_response("user_passwd.html",locals())
def result_passwd(request):
    if request.method == 'GET':
        username = request.GET['username']
        old_password = request.GET['old_password']
        new_password = request.GET['new_password']
        userinfo = User.objects.get(username=request.user)
        user = auth.authenticate(username=username,password=old_password)
        if user is not None:
            if username == userinfo.username:
                newuser = User.objects.get(username=username)
                newuser.set_password(new_password)
                newuser.save()
                logger.error(str(request.user)+' - '+'ChangePassword'+ ' - success!')
                return HttpResponse('ok')
            else:
                logger.error(str(request.user)+' - '+'ChangePassword'+ ' - privileges error!')
                return HttpResponse('No')
        elif userinfo.is_superuser:
            newuser = User.objects.get(username=username)
            newuser.set_password(new_password)
            newuser.save()
            logger.error(str(request.user)+' - '+'ChangePassword'+ ' - success!')
            return HttpResponse('ok')
        else:
            logger.error(str(request.user)+' - '+'ChangePassword'+ ' - Password error!')
            return HttpResponse('False')
def log_list_offline(request):
    if request.method == 'GET':
        Login_Info = Login_Record.objects.all().order_by('-id')[0:99]
        contact_list,p, contacts, page_range, current_page, show_first, show_end=pages(Login_Info,request)
        return render_to_response('log_list_offline.html', locals())
def log_list_cmd(request):
    if request.method == 'GET':
        cmd_info = cmd_record.objects.all().order_by('-id')[0:99]
        contact_list,p, contacts, page_range, current_page, show_first, show_end=pages(cmd_info,request)
        return render_to_response('log_list_cmd.html',locals())
def log_list_file(request):
    if request.method == 'GET':
        file_record = File_Record.objects.all().order_by('-id')[0:99]
        contact_list,p, contacts, page_range, current_page, show_first, show_end=pages(file_record,request)
        return render_to_response('log_list_file.html',locals())
def log_search(request):
    keyword = request.POST['keyword']
    offset = request.POST['offset']
    if offset == 'offline':
        Login_Info = Login_Record.objects.filter(Q(name__icontains=keyword) | Q(ip__icontains=keyword))
        contact_list,p, contacts, page_range, current_page, show_first, show_end=pages(Login_Info,request)
    if offset == 'file':
        file_record = File_Record.objects.filter(Q(hostname__icontains=keyword) | Q(name__icontains=keyword) | Q(filename__icontains=keyword) | Q(ip__icontains=keyword) | Q(file_type__icontains=keyword))
        contact_list,p, contacts, page_range, current_page, show_first, show_end=pages(file_record,request)
    if offset == 'cmd':
        cmd_info = cmd_record.objects.filter(Q(hostname__icontains=keyword) | Q(name__icontains=keyword) |Q(ip__icontains=keyword) | Q(cmd__icontains=keyword))
        contact_list,p, contacts, page_range, current_page, show_first, show_end=pages(cmd_info,request)
    return render_to_response('log_list_%s.html' % offset, locals())
def user_search(request):
    keyword = request.POST['keyword']
    User_info= User.objects.filter(Q(username__icontains=keyword) | Q(email__icontains=keyword) | Q(is_active__icontains=keyword))
    contact_list,p, contacts, page_range, current_page, show_first, show_end=pages(User_info,request)
    return render_to_response('user.html',locals())
