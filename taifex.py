import requests
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

font = FontProperties(fname = r'MSYH.TTC')
url = "https://www.taifex.com.tw/cht/3/pcRatio"
payload = {
    "queryStartDate": "2024/05/13",
    "queryEndDate": "2024/06/12"
}
res = requests.get(url, params = payload)
df = pd.read_html(res.text)[0]
df['日期'] = pd.to_datetime(df['日期'])
df = df.sort_values('日期').reset_index(drop = True)
plt.figure(figsize = (6, 3))
plt.plot(df['日期'], df['買賣權未平倉量比率%'])
plt.xticks(rotation = 30)
plt.legend(['買賣權未平倉量比率%'], prop = font, fontsize = 12)
plt.xlabel('日期', fontproperties = font, fontsize = 12)
plt.ylabel('買賣權未平倉量比率%', fontproperties = font, fontsize = 12)
plt.title('買賣權未平倉量比率%', fontproperties = font, fontsize = 14)
plt.savefig('pcratio.png', dpi = 200, bbox_inches = 'tight')

content = '''
## {} 選擇權 Put/Call Ratios
![](pcratio.png)
'''
with open('README.md', 'w') as f:
    f.write(content.format(dt.datetime.today().strftime('%Y/%m/%d')))
