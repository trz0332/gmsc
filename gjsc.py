# -*- coding: UTF-8 -*-
from xb_redisapi import xb_redis
import re,struct,math
import sys
import logging
import threading,time
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_tcp
import yaml
from xblog import logger2 as log2
data={}
init_flag=0
vison='1.2.1'
logger = modbus_tk.utils.create_logger(name="console", record_format="%(message)s")

def changeTime(allTime):  
    day = 24*60*60  
    hour = 60*60  
    min = 60  
    if allTime <60:          
        return  "%d 秒"%math.ceil(allTime)  
    elif  allTime > day:  
        days = divmod(allTime,day)   
        return "%d 天 %s"%(int(days[0]),changeTime(days[1]))  
    elif allTime > hour:  
        hours = divmod(allTime,hour)  
        return '%d 时 %s'%(int(hours[0]),changeTime(hours[1]))  
    else:  
        mins = divmod(allTime,min)  
        return "%d 分 %d 秒"%(int(mins[0]),math.ceil(mins[1]))

    
def mb_set_float(b_name,addr,val):   #写入flaot格式数据
    j=struct.unpack('>HH',struct.pack('>f',val))
    slave_1.set_values(b_name,addr,j)

def getdata(ts,listid):  #获取数据
        global data
        global init_flag
        while 1:
            t1=time.time()
            try:
                datalist=ts.getmkey(listid)  #从redis接口获取数据，返回一个list
            except Exception as e:
                slave_1.set_values('1',0,0)  #如果运行失败modbus  col值地址1设置0
                log2.info('连接redis失败,1分钟后重试')
                log2.info(e)
                init_flag=0
                time.sleep(60)  #1分钟后重连
            else:
                slave_1.set_values('1',0,1)  #返回正常，col值设置位1
                for index,item in enumerate(listid):
                    data[item]=datalist[index]  #把获取到的值生成对应的字典key为id
                log2.info(data)
                init_flag=1
                log2.info('获取redis耗时{}'.format(time.time()-t1))  #计算本次获取用时
                time.sleep(config['server']['delay'])
def runsc(slave):
    t_x=time.time()
    time.sleep(2)
    while 1:
        if init_flag:  #如果redis连接正常执行
            t11=time.time()
            for i in scrept:  #获取脚本迭代
                keydata=i[list(i.keys())[0]]
                gs=keydata['gs']  #获取脚本文本
                p1=re.compile(r'[{](.*?)[}]', re.S)  #最小规则，查找括号内容
                aa=re.findall(p1, gs)  #执行查找，返回测点ID的key
                for x in aa:
                    gs=gs.replace(x,"data['{}']".format(x))  #把脚本内的key换成 data['{}']对应的内容
                gs="locals()[\'value\']= "+re.sub('[{}]', '', gs)  #添加头value=
                exec(gs)  #执行脚本语句
                datemdbus=locals()['value']  #获得脚本语句执行后的结果
                if keydata['type']=='int':  #如果类型为int  设置COILS地址的值
                    slave.set_values('1',keydata['adr'],datemdbus)
                elif keydata['type']=='float':  #如果类型为float 设置HOLDING_REGISTERS地址的值
                    mb_set_float('0',keydata['adr'],datemdbus)
            log2.info('写入modbus点表耗时{}'.format(time.time()-t11))  #计算写入modbus耗时
            time.sleep(config['slave']['delay'])
        else:
            log2.info('连接redis失败，等待redis连接成功，暂停modbus数据刷新')  #如果redis连接失败，30s后重试mosbus数据更新
            time.sleep(10)
        time.sleep(4)  #正常运行没4秒更新modbus数据


def main():
    try:
        server.start()    #modbus服务开始
        t_x=time.time()
        while True:
            #print('当前已经运行{}'.format(changeTime(time.time()-t_x)),end='\r') 
            #print('当前已经运行{}'.format(changeTime(time.time()-t_x)))
            cmd = sys.stdin.readline()
            args = cmd.split(' ')
            if cmd.find('quit') == 0:
                sys.stdout.write('bye-bye\r\n')
            #    #break 
            time.sleep(60) 
    finally:
        server.stop()

#############解析配置文件#############################
def loadconfig(filename='zhoubao_config.yaml'):   #导入配置
    f=open(filename,'r',encoding='utf-8')
    try:
        config=yaml.load(f)
    except:
        return False
    else:
        return config
def jxconfig(config):  #解析培训hi文件
    sidlist=[]
    MAXADR_C=0
    MAXADR_R=0
    for i in config['scrept']:
        #################算出所有需要采集的测点ID
        keydata=i[list(i.keys())[0]]
        gs=keydata['gs']
        p1=re.compile(r'[{](.*?)[}]', re.S) 
        aa=re.findall(p1, gs) 
        for idi in aa:
            if idi not in sidlist:
                sidlist.append(idi)
        ###############    #########计算最大的adr地址
        if keydata['type']=='float' and  keydata['adr']>MAXADR_R:
            MAXADR_R=keydata['adr'] 
        elif keydata['type']=='int' and  keydata['adr']>MAXADR_C:
            MAXADR_C=keydata['adr']
    return MAXADR_R,MAXADR_C,sidlist

#############################
logger.info("-"*50)
logger.info("作者:谭润芝")
logger.info("联系电话：13267153721")
logger.info("联系邮箱：trz0332@163.com")
logger.info("版本:{}".format(vison))
logger.info("-"*50)
#############################
runflag=0
log2.info('开始导入配置文件')
logger.info('开始导入配置文件')
config=loadconfig('config.yaml')
if config:
    time.sleep(1)
    scrept=config['scrept']
    l1,l2,l3=jxconfig(config)
    logger.info('导入配置文件成功\n总共获取{}条规则\n需要从共\
济平台获取{}个测点'.format(len(config['scrept']),len(l3)))
    log2.info('导入配置文件成功\n总共获取{}条规则\n需要从共\
济平台获取{}个测点'.format(len(config['scrept']),len(l3)))
    runflag=1

logger.info('redis服务器:{}\nredis端口:{}'.format(config['server']['host'],config['server']['port']))
logger.info('modbus端口:{}\nmodbus地址:{}'.format(config['slave']['port'],config['slave']['adr']))
logger.info(('-'*50))
logger.info('初始化modbus服务器')
log2.info('初始化modbus服务器')
server = modbus_tcp.TcpServer(port=config['slave']['port'])  #定义modbusserver参数
logger.info('创建modbuss—slave')
log2.info('创建modbuss—slave')
slave_1 = server.add_slave(config['slave']['adr'])
logger.info('创建HOLDING_REGISTERS数据集')
log2.info('创建HOLDING_REGISTERS数据集')
slave_1.add_block('0', cst.HOLDING_REGISTERS, 0, l1+2)  #生成数据块0
logger.info('创建COILS数据集')
log2.info('创建COILS数据集')
slave_1.add_block('1', cst.COILS, 0, l2+2)  #生成数据块1
logger.info('完成modbus初始化')
log2.info('完成modbus初始化')
logger.info('-'*50)
log2.info('-'*50)
logger.info('开始初始化redis')
log2.info('开始初始化redis')
ts=xb_redis(config['server']['host'],config['server']['port'])  #定义redis服务
logger.info('完成初始化redis')
log2.info('完成初始化redis')
time.sleep(2)
logger.info('-'*50)
log2.info('-'*50)

if runflag==1:  #如果运行标志正常
    threads = []
    t2 = threading.Thread(target=getdata,args=(ts,l3,))  #添加redis获取线程
    threads.append(t2)
    logger.info('添加连接共济平台线程 ')
    log2.info('添加连接共济平台线程')
    t4=  threading.Thread(target=main)  #添加modbusserver线程
    threads.append(t4)
    logger.info('添加modbus服务线程')
    log2.info('添加modbus服务线程')
    t3 = threading.Thread(target=runsc,args=(slave_1,))  #添加刷新modbusserver数据线程
    threads.append(t3)
    logger.info('添加脚本运行线程')
    log2.info('添加脚本运行线程')
    for i in threads:
        i.setDaemon(True)
        i.start()
    #logger.info('程序已经正常启动')
    i.join()  #启动所有线程
else:
    logger.info('程序自检错误，无法执行')
    log2.info('程序自检错误，无法执行')