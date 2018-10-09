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



init_flag=0
data={}
logger = modbus_tk.utils.create_logger(name="console", record_format="%(message)s")
vison='1.3.1'
lc=locals()


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

def loadconfig(filename='zhoubao_config.yaml'):   #导入配置
    f=open(filename,'r',encoding='utf-8')
    try:
        lc['config']=yaml.load(f)
    except:
        return False

def jxconfig():
    sidlist=[]
    lc['dirv']=[i for i in config['scrept']]
    for i in config['scrept']:
        lc[i]=[]
        MAXADR_R=0
        MAXADR_C=0
        for x in config['scrept'][i][1:]:
        #################算出所有需要采集的测点ID
            keydata=x[list(x.keys())[0]]
            gs=keydata['gs']
            p1=re.compile(r'[{](.*?)[}]', re.S) 
            aa=re.findall(p1, gs) 
            for idi in aa:
                if idi not in lc[i]:
                    lc[i].append(idi)
            if keydata['type']=='float' and  keydata['adr']>MAXADR_R:
                MAXADR_R=keydata['adr'] 
            elif keydata['type']=='int' and  keydata['adr']>MAXADR_C:
                MAXADR_C=keydata['adr']
        config['scrept'][i].append({'maxadr_r':MAXADR_R})
        config['scrept'][i].append({'maxadr_c':MAXADR_C})
        logger.info('设备:{},地址{}。有{}条规则,MODBUS地址HOLDING_REGISTERS长度{},MODBUS地址COILS长度{}'.format(\
                i,config['scrept'][i][0]['adr'],len(lc[i])\
                    ,config['scrept'][i][-2]['maxadr_r'],config['scrept'][i][-1]['maxadr_c'])
                ,)
        log2.info('设备:{},地址{}。有{}条规则,MODBUS地址HOLDING_REGISTERS长度{},MODBUS地址COILS长度{}'.format(\
                i,config['scrept'][i][0]['adr'],len(lc[i])\
                    ,config['scrept'][i][-2]['maxadr_r'],config['scrept'][i][-1]['maxadr_c'])
                ,)
        sidlist+=lc[i]
    logger.info('总共需要获取{}个测点'.format(len(sidlist)))
    log2.info('总共需要获取{}个测点'.format(len(sidlist)))
    return sidlist

def creatmodbusslave(server):
    for i in config['scrept']:
        logger.info('创建{}地址{}的数据块'.format(i,config['scrept'][i][0]['adr']))
        log2.info('创建{}地址{}的数据块'.format(i,config['scrept'][i][0]['adr']))
        lc[i+'slave']=server.add_slave(config['scrept'][i][0]['adr'])
        lc[i+'slave'].add_block(i+'r', cst.HOLDING_REGISTERS, 0, config['scrept'][i][-2]['maxadr_r']+2)
        lc[i+'slave'].add_block(i+'c', cst.COILS, 0, config['scrept'][i][-1]['maxadr_c']+2)

def getdata(ts,listid):  #获取数据
        global data
        global init_flag
        while 1:
            t1=time.time()
            try:
                datalist=ts.getmkey(listid)  #从redis接口获取数据，返回一个list
            except Exception as e:  #如果运行失败modbus  col值地址1设置0
                for i in dirv:
                    lc[i+'slave'].set_values(i+'c',0,0)
                log2.info('连接redis失败,1分钟后重试')
                log2.info(e)
                init_flag=0
                time.sleep(60)  #1分钟后重连
            else:
                for i in dirv:
                    lc[i+'slave'].set_values(i+'c',0,1)  #返回正常，col值设置位1
                for index,item in enumerate(listid):
                    data[item]=datalist[index]  #把获取到的值生成对应的字典key为id
                #log2.info(data)
                init_flag=1
                log2.info('获取redis耗时{}'.format(time.time()-t1))  #计算本次获取用时
                time.sleep(config['server']['redis_delay'])

def mb_set_float(slave,b_name,addr,val):   #写入flaot格式数据
    j=struct.unpack('>HH',struct.pack('>f',val))
    slave.set_values(b_name,addr,j)

def runsc(dirv_i):
    t_x=time.time()
    time.sleep(2)
    scrept=config['scrept']
    while 1:
        if init_flag:  #如果redis连接正常执行
            t11=time.time()
            for i in scrept[dirv_i][1:-2]:  #获取脚本迭代
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
                    lc[dirv_i+'slave'].set_values(dirv_i+'c',keydata['adr'],datemdbus)
                elif keydata['type']=='float':  #如果类型为float 设置HOLDING_REGISTERS地址的值
                    mb_set_float(lc[dirv_i+'slave'],dirv_i+'r',keydata['adr'],datemdbus)
            log2.info('{}写入modbus点表耗时{}'.format(dirv_i+'slave',time.time()-t11))  #计算写入modbus耗时
            time.sleep(config['server']['modbus_delay'])
        else:
            log2.info('连接redis失败，等待redis连接成功，暂停modbus数据刷新')  #如果redis连接失败，30s后重试mosbus数据更新
            time.sleep(10)
        time.sleep(config['server']['modbus_delay'])  #正常运行没4秒更新modbus数据


def main():
    try:
        server.start()    #modbus服务开始
        t_x=time.time()
        while True:
            try:
                #print('当前已经运行{}'.format(changeTime(time.time()-t_x)),end='\r') 
                sys.stdout.writelines(' '*50 + '\r')
                sys.stdout.writelines('当前已经运行{}'.format(changeTime(time.time()-t_x)) + '\r')
            except:time.sleep(1) 
            else:
                #print('当前已经运行{}'.format(changeTime(time.time()-t_x)))
                #cmd = sys.stdin.readline()
                #args = cmd.split(' ')
                #if cmd.find('quit') == 0:
                #    sys.stdout.write('bye-bye\r\n')
                #    #break 
                time.sleep(1) 
    finally:
        server.stop()

if __name__=='__main__':

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
    loadconfig('config.yaml')
    logger.info('redis服务器:{}\nredis端口:{}'.format(config['server']['redis_host'],config['server']['redis_port']))
    logger.info('modbus端口:{}'.format(config['server']['modbus_port']))
    log2.info('redis服务器:{}\nredis端口:{}'.format(config['server']['redis_host'],config['server']['redis_port']))
    log2.info('modbus端口:{}'.format(config['server']['modbus_port']))
    runflag=1
    l3=jxconfig()
    log2.info('导入配置文件成功')
    logger.info('导入配置文件成功')
    logger.info(('-'*50))
    logger.info('初始化modbus服务器')
    log2.info('初始化modbus服务器')
    server = modbus_tcp.TcpServer(port=config['server']['modbus_port'])
    creatmodbusslave(server)
    logger.info('完成modbus服务器初始化')
    log2.info('完成modbus服务器初始化')
    logger.info(('-'*50))
    logger.info('开始初始化redis')
    log2.info('开始初始化redis')
    ts=xb_redis(config['server']['redis_host'],config['server']['redis_port'])  #定义redis服务
    logger.info('初始化redis成功')
    log2.info('初始化redis成功')
    logger.info(('-'*50))
    if runflag==1:  #如果运行标志正常
        threads = []
        logger.info('创建redis采集线程')
        log2.info('创建redis采集线程')
        t2 = threading.Thread(target=getdata,args=(ts,l3,))  #添加redis获取线程
        threads.append(t2)
        logger.info('创建modbus服务线程')
        log2.info('创建modbus服务线程')
        t4=  threading.Thread(target=main)  #添加modbusserver线程
        threads.append(t4)
        for i in dirv:
              #添加刷新modbusserver数据线程
            logger.info('创建modbus设备{}刷新线程'.format(i))
            log2.info('创建modbus设备{}刷新线程'.format(i))
            threads.append(threading.Thread(target=runsc,args=(i,)))
        logger.info(('-'*50))
        for x in threads:
            x.setDaemon(True)
            x.start()
        #logger.info('程序已经正常启动')
        x.join()  #启动所有线程
#    else:
#        logger.info('程序自检错误，无法执行')
#        log2.info('程序自检错误，无法执行')

























