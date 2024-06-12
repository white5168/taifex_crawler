import requests
import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'Microsoft Yahei'
url = "https://www.taifex.com.tw/cht/3/pcRatio"
payload = {
    "queryStartDate": "2024/05/13",
    "queryEndDate": "2024/06/12"
}
res = requests.get(url, params = payload)
df = pd.read_html(res.text)[0]
df['日期'] = pd.to_datetime(df['日期'])
df = df.sort_values('日期').reset_index(drop = True)
df.plot(x = '日期', y = '買賣權未平倉量比率%', figsize = (5, 3))
plt.savefig('pcratio.png', dpi = 200, bbox_inches = 'tight')