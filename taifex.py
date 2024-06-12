import requests
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from dateutil.relativedelta import relativedelta
import time

today = dt.datetime.today().strftime('%Y%m%d')
font = FontProperties(fname = r'MSYH.TTC')
url = "https://www.taifex.com.tw/cht/3/pcRatio"
payload = {
    'down_type':'',
    'queryStartDate': '2024/05/13',
    'queryEndDate': '2024/06/12'
}

data = []
base = dt.datetime.today() - relativedelta(months = 6)
while base <= dt.datetime.today():
    payload['queryStartDate'] = base.replace(day = 1).strftime('%Y/%m/%d')
    payload['queryEndDate'] = (base.replace(day = 1) + 
               relativedelta(months = 1) - 
               relativedelta(days = 1)).strftime('%Y/%m/%d')

    res = requests.post(url, data = payload)
    data.append(pd.read_html(res.text)[0])
    time.sleep(5)
    base += relativedelta(months = 1)

df = pd.concat(data)
df['日期'] = pd.to_datetime(df['日期'])
df = df.sort_values('日期').reset_index(drop = True)
plt.figure(figsize = (6, 3))
plt.plot(df['日期'], df['買賣權未平倉量比率%'])
plt.xticks(rotation = 30)
plt.legend(['買賣權未平倉量比率%'], prop = font, fontsize = 12)
plt.xlabel('日期', fontproperties = font, fontsize = 12)
plt.ylabel('買賣權未平倉量比率%', fontproperties = font, fontsize = 12)
plt.title('{}買賣權未平倉量比率%'.format(today), fontproperties = font, fontsize = 14)
plt.savefig('pcratio.png', dpi = 200, bbox_inches = 'tight')

content = '''
## {} 選擇權 Put/Call Ratios
![](pcratio.png)
'''
with open('README.md', 'w') as f:
    f.write(content.format(today))
