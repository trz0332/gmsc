from xb_redisapi import xb_redis
import re,struct
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



logger = modbus_tk.utils.create_logger(name="console", record_format="%(message)s")


    
def mb_set_float(b_name,addr,val):   #写入flaot格式数据
    j=struct.unpack('>HH',struct.pack('>f',val))
    slave_1.set_values(b_name,addr,j)

def getdata(ts,l1):  #获取数据
        global data
        global init_flag
        while 1:
            t1=time.time()
            try:
                datalist=ts.getmkey(l1)  #从redis接口获取数据，返回一个list
            except Exception as e:
                slave_1.set_values('1',0,0)  #如果运行失败modbus  col值地址1设置0
                log2.info('连接redis失败,1分钟后重试')
                log2.info(e)
                init_flag=0
                time.sleep(60)  #1分钟后重连
            else:
                slave_1.set_values('1',0,1)  #返回正常，col值设置位1
                for index,item in enumerate(l1):
                    data[item]=datalist[index]  #把获取到的值生成对应的字典key为id
                log2.info(data)
                init_flag=1
                log2.info('获取redis耗时{}'.format(time.time()-t1))  #计算本次获取用时
                time.sleep(5)
def runsc(slave):
    while 1:
        if init_flag:  #如果redis连接正常执行
            t11=time.time()
            for i in scrept:  #获取脚本迭代
                gs=scrept[i]['gs']  #获取脚本文本
                p1=re.compile(r'[{](.*?)[}]', re.S)  #最小规则，查找括号内容
                aa=re.findall(p1, gs)  #执行查找，返回测点ID的key
                for x in aa:
                    gs=gs.replace(x,"data['{}']".format(x))  #把脚本内的key换成 data['{}']对应的内容
                gs="locals()[\'value\']= "+re.sub('[{}]', '', gs)  #添加头value=
                exec(gs)  #执行脚本语句
                datemdbus=locals()['value']  #获得脚本语句执行后的结果
                if scrept[i]['type']=='int':  #如果类型为int  设置COILS地址的值
                    slave.set_values('1',scrept[i]['adr'],datemdbus)
                elif scrept[i]['type']=='float':  #如果类型为float 设置HOLDING_REGISTERS地址的值
                    mb_set_float('0',scrept[i]['adr'],datemdbus)
            log2.info('写入modbus点表耗时{}'.format(time.time()-t11))  #计算写入modbus耗时
        else:
            log2.info('连接redis失败，等待redis连接成功，暂停modbus数据刷新')  #如果redis连接失败，30s后重试mosbus数据更新
            time.sleep(30)
        time.sleep(4)  #正常运行没4秒更新modbus数据



def main():
    try:
        server.start()    #modbus服务开始
        while True:
            cmd = sys.stdin.readline()
            args = cmd.split(' ')
            if cmd.find('quit') == 0:
                sys.stdout.write('bye-bye\r\n')
                break   
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
    modbuslen=0
    sidlist=[]
    for i in config['scrept']:
        #################算出所有需要采集的测点ID
        gs=config['scrept'][i]['gs']
        p1=re.compile(r'[{](.*?)[}]', re.S) 
        aa=re.findall(p1, gs) 
        for idi in aa:
            if idi not in sidlist:
                sidlist.append(idi)
        ###############
        if config['scrept'][i]['type']=='float':  #计算modbus
            modbuslen+=2
        elif config['scrept'][i]['type']=='int':
            modbuslen+=1
    return modbuslen,sidlist

#############################
runflag=0
log2.info('开始导入配置文件{}'.format('-'*100))
print('开始导入配置文件{}'.format('-'*100))
config=loadconfig('config.yaml')
if config:
    time.sleep(1)
    scrept=config['scrept']
    l1,l2=jxconfig(config)
    print('导入配置文件成功,总共获取{}条规则，modbus点位长度{},需要从共\
        济平台获取{}个测点'.format(len(config['scrept']),l1,len(l2)))
    log2.info('导入配置文件成功,总共获取{}条规则，modbus点位长度{},需要从共\
        济平台获取{}个测点'.format(len(config['scrept']),l1,len(l2)))
    #########计算最大的adr地址
    MAXADR_C=0
    MAXADR_R=0
    for i in scrept:
        if config['scrept'][i]['type']=='float' and  config['scrept'][i]['adr']>MAXADR_R:
            MAXADR_R=config['scrept'][i]['adr'] 
        elif config['scrept'][i]['type']=='int' and  config['scrept'][i]['adr']>MAXADR_C:
            MAXADR_C=config['scrept'][i]['adr']
    runflag=1
print('---------------------\n\
redis服务器{}端口{}\n\
modbus端口{}地址{}\n\
---------------------'.format(config['server']['host'],config['server']['port'],config['slave']['port'],config['slave']['adr']))
print('初始化modbus服务器{}'.format('_'*100))
log2.info('初始化modbus服务器{}'.format('_'*100))
server = modbus_tcp.TcpServer(port=config['slave']['port'])  #定义modbusserver参数
logger.info("running...")


slave_1 = server.add_slave(config['slave']['adr'])
slave_1.add_block('0', cst.HOLDING_REGISTERS, 0, MAXADR_R+2)  #生成数据块0
slave_1.add_block('1', cst.COILS, 0, MAXADR_C+2)  #生成数据块1
print('开始初始化redis{}'.format('-'*100))
log2.info('开始初始化redis{}'.format('-'*100))
ts=xb_redis(config['server']['host'],config['server']['port'])  #定义redis服务
time.sleep(2)

if runflag==1:  #如果运行标志正常
    threads = []
    t2 = threading.Thread(target=getdata,args=(ts,l2,))  #添加redis获取线程
    threads.append(t2)
    print('添加连接共济平台线程 ')
    log2.info('添加连接共济平台线程')
    t4=  threading.Thread(target=main)  #添加modbusserver线程
    threads.append(t4)
    print('添加modbus服务线程')
    log2.info('添加modbus服务线程')
    t3 = threading.Thread(target=runsc,args=(slave_1,))  #添加刷新modbusserver数据线程
    threads.append(t3)
    print('添加脚本运行线程')
    log2.info('添加脚本运行线程')
    if __name__ == "__main__":
        for i in threads:
            i.setDaemon(True)
            i.start()
        i.join()  #启动所有线程
else:
    print('程序自检错误，无法执行')
    log2.info('程序自检错误，无法执行')