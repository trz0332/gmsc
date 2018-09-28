import redis
import re
import struct
from xblog import logger2 as log2
class xb_redis():
    def __init__(self,host,port):
        self.host=host
        self.port=port
        self.rds=redis.StrictRedis(self.host,port=self.port)
    def id2id(self,a):
        aa=re.split('[SEAD]', a)[1:]
        if a.find('D')==-1:
            aat='S{}.E{}.A{}'.format(aa[0],aa[1],aa[2])
        else:
            aat='S{}.E{}.D{}'.format(aa[0],aa[1],aa[2])
        return aat.encode('utf8')
    def getonekey(self,key):
        idt=self.id2id(key)
        data=self.rds.get(idt)
        if data:
            return self.jx(data)

    def getmkey(self,key):
        key1=[]
        for i in key:
            key1.append(self.id2id(i))
        data=self.rds.mget(key1)
        data1=[]
        for index,item in enumerate(data):
            if item :
                data1.append(self.jx(item))
            else:
                log2.debug('{}没有获取到数据'.format(key[index]))
                data1.append(0)
        return data1

    def jx(self,v1):
        if v1:
            len1=v1[0]
            sid=str(v1[1:len1+1],'gbk')
            if sid.find('D') !=-1:
                len2=v1[1+len(sid)+7]
                stat=v1[1+len(sid)+7+1:1+len(sid)+7+1+len2]
                stat_z=v1[-2]
                return stat_z
            elif sid.find('A') !=-1:
                data=v1[1+len(sid)+7:1+len(sid)+7+8]
                return struct.unpack('d',data)[0]
        else :return None



    def jxdi(self,v1):
        len1=v1[0]
        sid=v1[1:len1+1]
        len2=v1[1+len(sid)+7]
        stat=v1[1+len(sid)+7+1:1+len(sid)+7+1+len2]
        stat_z=v1[-2]
        return (str(sid,'gbk'),str(stat,'gbk'),stat_z)


    def jxai(self,v1):
        len1=v1[0]
        sid=str(v1[1:len1+1],'gbk')
        data=v1[1+len(sid)+7:1+len(sid)+7+8]
        return sid,struct.unpack('d',data)
if __name__=='__main__':
    ts=xb_redis('107.151.172.213',10070)
    l1=['S12E51A1','S12E52A1','S12E53A1','S12E54A1','S12E55A1','S12E56A1','S12E57A1','S12E58A1']
    print(ts.getmkey(l1))
