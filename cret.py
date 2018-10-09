# -*- coding: UTF-8 -*-
from openpyxl import *
import yaml

wb=load_workbook('阿里功耗统计.xlsx')
ws=wb['功率最大值']
vl=ws['a2:d890']
fadr=1
cadr=1
d1=[]
for i in vl :
    if i[3].    value:
        scrept={}
        scrept[('{}{}机柜功率'.format(i[0].value,i[1].value))]={'gs': "{%s}+{%s}"%(i[2].value,i[3].value),
    'adr': fadr,'type': 'float'
    }
        d1.append(scrept)
        scrept={}
        scrept['{}{}机柜功率比'.format(i[0].value,i[1].value)]={'gs': "({%s}+{%s})/0.03"%(i[2].value,i[3].value),
    'adr': fadr+2,'type': 'float'
    }
        d1.append(scrept)
        scrept={}
        fadr+=4
        scrept['{}{}机柜功率超限80'.format(i[0].value,i[1].value)]={'gs': "0 if ({%s}+{%s})/0.03<80 else 1"%(i[2].value,i[3].value),
    'adr': cadr,'type': 'int'
    }
        d1.append(scrept)
        scrept={}
        scrept['{}{}机柜功率超限100'.format(i[0].value,i[1].value)]={'gs': "0 if ({%s}+{%s})/0.03<100 else 1"%(i[2].value,i[3].value),
    'adr': cadr+1,'type': 'int'
    }
        d1.append(scrept)
        scrept={}
        scrept['{}{}机柜功率超限110'.format(i[0].value,i[1].value)]={'gs': "0 if ({%s}+{%s})/0.03<110 else 1"%(i[2].value,i[3].value),
    'adr': cadr+2,'type': 'int'
    }
        d1.append(scrept)
        cadr+=3
print(scrept)
data={'scrept':d1}
data2={'scrept':data}
def savehostname(data):    #保存配置
    with open('tt.yaml', 'w+') as stream:
        try:
            yaml.dump(data, stream,default_flow_style=False,encoding='utf-8',allow_unicode=True)
        except:return False
        else:return True
savehostname(data2)

