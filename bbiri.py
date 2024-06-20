# coding: utf-8
import requests
import pandas as pd
from io import StringIO
from dateutil.relativedelta import relativedelta
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import threading
import sys
import traceback

def countdown(t):
    while -1 < t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        if t > 0:
            print(timer, end="\r")
        elif t == 0:
            print(timer, end="\n")
        threading.Event().wait(1)
        #time.sleep(1)
        t -= 1
        
def getTXFSettlementDate():
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}
    url = "https://spreadsheets.google.com/tq?tqx=out:html&tq=select+A&key=1LviX5-yi06R_dOET13piHQX0KQDFU-5QDpFIvvxRpEo&gid=0"
    res = requests.get(url, headers = headers)
    return pd.read_html(StringIO(res.text), header = 0, parse_dates = ['台指結算日'])[0]

def getTXMTX(base, today):
    url = "https://www.taifex.com.tw/cht/3/futDataDown"
    payload = {
        'down_type': 1,
        'commodity_id': 'TX',
        'queryStartDate': '2024/02/01',
        'queryEndDate': '2024/02/29'
    }
    TX, MTX = [], []
    while base <= today:
        startdate = base.replace(day = 1).strftime("%Y/%m/%d")
        enddate = (base.replace(day = 1) + 
                   relativedelta(months = 1) -
                   relativedelta(days = 1)).strftime("%Y/%m/%d")
        print(startdate, enddate)        
        payload['queryStartDate'] = startdate
        payload['queryEndDate'] = enddate

        payload['commodity_id'] = 'TX'
        err_count = 0
        while True:
            try:
                res = requests.get(url, params = payload)
            except Exception as e:
                sys_type, sys_value, sys_obj = sys.exc_info()
                print("sys_type:", sys_type)
                print("sys_value:", sys_value)
                print("sys_obj:", sys_obj)
                exp = traceback.extract_tb(sys_obj)
                print("file:", exp[0][0])
                print("line:", exp[0][1])
                print("module:", exp[0][2])
                
                err_count += 1
                print("錯誤:", err_count)
                countdown(3)
                continue
            else:
                break        

        df = pd.read_csv(StringIO(res.text), index_col = False)
        df = df[df['收盤價'].str.strip() != '-']
        df = df[(df['到期月份(週別)'].str.find('/') == -1) & (df['交易時段'].str.strip() == '一般')]
        TX.append(df.apply(pd.to_numeric, errors = 'ignore'))

        payload['commodity_id'] = 'MTX'  
        err_count = 0
        while True:
            try:
                res = requests.get(url, params = payload)
            except Exception as e:
                sys_type, sys_value, sys_obj = sys.exc_info()
                print("sys_type:", sys_type)
                print("sys_value:", sys_value)
                print("sys_obj:", sys_obj)
                exp = traceback.extract_tb(sys_obj)
                print("file:", exp[0][0])
                print("line:", exp[0][1])
                print("module:", exp[0][2])
                
                err_count += 1
                print("錯誤:", err_count)
                countdown(3)
                continue
            else:
                break 
        df = pd.read_csv(StringIO(res.text), index_col = False)
        df = df[df['收盤價'].str.strip() != '-']
        df = df[(df['到期月份(週別)'].str.find('/') == -1) & (df['交易時段'].str.strip() == '一般')]
        MTX.append(df.apply(pd.to_numeric, errors = 'ignore').groupby(['交易日期'])['未沖銷契約數'].sum())
        base += relativedelta(months = 1)

    df1 = pd.concat(TX).groupby('交易日期')['收盤價'].first()
    df2 = pd.concat(MTX).copy()#未沖銷契約數
    return df1, df2

def getBBIRI(df1, df2, base):
    url = "https://www.taifex.com.tw/cht/3/futContractsDateDown"
    payload = {
        'queryStartDate': base.strftime("%Y/%m/%d"),
        'queryEndDate': dt.datetime.today().strftime("%Y/%m/%d"),
        'commodityId': 'MXF'
    }

    now = dt.datetime.now() 
    if now < dt.datetime(now.year, now.month, now.day, 16, 0, 0):
        payload['queryEndDate'] = (dt.datetime.today() - relativedelta(days = 1)).strftime("%Y/%m/%d")

    res = requests.get(url, params = payload)
    df = pd.read_csv(StringIO(res.text))
    df3 = df.groupby('日期')['多空未平倉口數淨額'].sum()
    df4 = df.groupby('日期')['多方未平倉口數'].sum().copy()
    df5 = df.groupby('日期')['空方未平倉口數'].sum().copy()
    df6 = pd.merge(df1, df2, left_index = True, right_index = True)
    df6 = pd.merge(df6, df4, left_index = True, right_index = True)
    df6 = pd.merge(df6, df5, left_index = True, right_index = True)
    df6 = pd.merge(df6, df3, left_index = True, right_index = True)
    df6['散戶多空比'] = df6['多空未平倉口數淨額'] / df6['未沖銷契約數'] * 100
    return df6

def drawFigure(df):
    font = FontProperties(fname = r'MSYH.TTC')
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(range(len(df.index)),
           df['散戶多空比'], 
           color = np.where(df['散戶多空比'] > 0, "r", "g"),
           width = 0.8,
           alpha = 0.6)
    ax.axhline(0, color = '#768498')
    ax.set_title("{} 散戶小台多空比".format(df.index[-1]), fontproperties = font, size = 14)
    ax.set_xlabel("日期", fontproperties = font, size = 12)
    ax.set_ylabel("散戶多空比(%)", fontproperties = font, size = 12)
    ax.set_xticks(range(0, len(df.index), 20))
    ax.set_xticklabels(df.index[::20], rotation = 30)

    ax2 = ax.twinx()
    ax2.plot(range(len(df.index)), df['收盤價'])
    ax2.set_xlim(-2, len(df.index) + 75)
    ax2.set_ylabel("台指期指數", 
                   labelpad = 20, 
                   fontproperties = font, 
                   rotation = -90,
                   size = 12)
    ax2.annotate("{}\n收盤價：{}".format(df.index[-1], df['收盤價'][df.index[-1]]), 
                xy = (len(df) - 2, df['收盤價'][df.index[-1]]),
                xytext = (len(df) + 10, df['收盤價'][df.index[-1]] * 0.96),
                #va ='top',
                color = "b",
                bbox = dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.3),
                arrowprops = dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='red'),
                fontproperties = font, 
                fontsize = 10)

    ax.annotate("{}\n散戶多空比：{:.2f}".format(df.index[-1], df['散戶多空比'][df.index[-1]]), 
                xy = (len(df) - 2, df['散戶多空比'][df.index[-1]]),
                xytext = (len(df) + 8, df['散戶多空比'][df.index[-1]] * 0.2),
                #va ='top',
                color = "r" if df['散戶多空比'][df.index[-1]] > 0 else "g",
                bbox = dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.3),
                arrowprops = dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='red'),
                fontproperties = font, 
                fontsize = 10)

    fig.savefig('bbiri.png', dpi = 200, bbox_inches = 'tight')
    
base = dt.datetime.today() - relativedelta(years = 1)
datelist = getTXFSettlementDate()
idx = datelist[datelist<base].dropna().index[-1]
base2 = datelist['台指結算日'][idx]
today = dt.datetime.today()
df1, df2 = getTXMTX(base2, today)
df = getBBIRI(df1, df2, base)
drawFigure(df)
