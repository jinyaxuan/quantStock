# coding=utf-8
from __future__ import print_function, absolute_import
from gm.api import *
import execjs
import requests
import json
import re
from urllib.parse import urlencode
import datetime

headers ={
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding":"gzip, deflate, br",
        "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "authorization":"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJOVGswTVE9PSIsImV4cCI6MTY3MTY3MTc0OH0.y3c6gv46vYIz-zb0U_YZALPmWOKZCOjWM9CIj3WtBAU",
        "Connection":"keep-alive",
        "origin": "https://dabanle.com",
        "Referer": "https://dabanle.com/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Mobile Safari/537.36 Edg/101.0.1210.53"
        }  

        
def Get_stock(stocks, black_stock):  

    url = 'https://api.heheapp.com/api/users_spool?name=pool-1'
    res = requests.get(headers=headers, url=url)
    res.enconding = "utf-8"
    query_res = json.loads(res.text)
    datas = query_res['data']
    for data in datas:
        if data['Code'][0] == '3' or data['Code'][0] == '0':
            stock = 'SZSE.' + data['Code']
        else:
            stock = 'SHSE.' + data['Code']
        
        if stock not in black_stock:
            stocks.append(stock)
    log(level='info', msg='获取首板股票列表:{}'.format(stocks), source='strategy')
    return stocks


def get_black_stock(black_stock):
    url = 'https://api.heheapp.com/api/users_black_list'
    res = requests.get(headers=headers, url=url)
    res.enconding = "utf-8"
    query_res = json.loads(res.text)
    datas = query_res['data']
    for data in datas:
        if data['Code'][0] == '3' or data['Code'][0] == '0':
            stock = 'SZSE.' + data['Code']
        else:
            stock = 'SHSE.' + data['Code']
        black_stock.append(stock)
        
    log(level='info', msg='获取黑名单列表成功！', source='strategy')
    return black_stock


# 策略中必须有init方法
def init(context):
    # algo_1(context)

    schedule(schedule_func=algo_1, date_rule='1d', time_rule='9:30:00')


def algo_1(context):

    context.black_stock = []
    context.stocks = []
    context.stocks_deal = {}
    context.frash_stock = 0

    context.black_stock = get_black_stock(context.black_stock)

    context.stocks = Get_stock(context.stocks, context.black_stock)

    context.instrument = get_instruments(symbols=context.stocks, df=True, fields='symbol, upper_limit')

    add_parameter(key='frash_stock', value=context.frash_stock, min=0, max=10, name='刷新股池', intro='刷新股池', group='刷新',
                readonly=False)

    subscribe(symbols=context.stocks, frequency='tick', count=5, wait_group=True, wait_group_timeout='6s',
              unsubscribe_previous=True)
    
def on_tick(context, tick):
    if tick.symbol not in context.stocks_deal.keys():
        context.stocks_deal[tick.symbol] = 0

    # unfinished = [i["symbol"] for i in get_unifished_orders()]
    upper_limit = context.instrument[context.instrument['symbol'] == tick.symbol].upper_limit.values[0]
    #获取交易状态

    if tick.price == upper_limit and context.stocks_deal[tick.symbol] == 0:
        order_percent(symbol=tick.symbol, percent=0.15, side=OrderSide_Buy, order_type=OrderType_Limit, position_effect=PositionEffect_Open, price=upper_limit)
        context.stocks_deal[tick.symbol] = 1
    
        log(level='info', msg='{}, 下单了'.format(tick.symbol), source='strategy')


def on_parameter(context, parameter):

    if parameter['name'] == '刷新股池' and parameter['value'] != context.frash_stock:

        context.frash_stock = parameter['value'] 
        set_parameter(key='frash_stock', value=context.frash_stock, min=0, max=1000, name='刷新股池', intro='刷新股池', group='刷新', readonly=False)

        unsubscribe(symbols=context.stocks, frequency='tick')

        context.stocks = []
        context.stocks = Get_stock(context.stocks, context.black_stock)
        context.instrument = get_instruments(symbols=context.stocks, df=True, fields='symbol, upper_limit')

        subscribe(symbols=context.stocks, frequency='tick', count=5, wait_group=True, wait_group_timeout='6s',
            unsubscribe_previous=True)

        log(level='info', msg='刷新股池', source='strategy')
    

def on_error(context, code, info):
    log(level='warning', msg='code:{}, info:{}'.format(code, info), source='strategy')

def on_execution_report(context, execrpt):

    log(level='info', msg='{}, 成交了'.format(execrpt.symbol), source='strategy')
    log(level='info', msg='成交回执:{}'.format(execrpt), source='strategy')

def on_order_status(context, order):
    
    if '资金不足' in order['ord_rej_reason_detail']:
        unsubscribe(symbols=order.symbol, frequency='tick')
        log(level='info', msg='资金不足，订阅取消', source='strategy')

    
    

if __name__ == '__main__':
    '''
        strategy_id策略ID, 由系统生成
        filename文件名, 请与本文件名保持一致
        mode运行模式, 实时模式:MODE_LIVE回测模式:MODE_BACKTEST
        token绑定计算机的ID, 可在系统设置-密钥管理中生成
        backtest_start_time回测开始时间
        backtest_end_time回测结束时间
        backtest_adjust股票复权方式, 不复权:ADJUST_NONE前复权:ADJUST_PREV后复权:ADJUST_POST
        backtest_initial_cash回测初始资金
        backtest_commission_ratio回测佣金比例
        backtest_slippage_ratio回测滑点比例
        '''
    run(strategy_id='b44a32ed-dbd6-11ec-9dd6-d85ed3030def',
        filename='main.py',
        mode=MODE_BACKTEST,
        token='7cf27f5eeede68e0ffefdd86071886bcf11258bb',
        backtest_start_time='2020-11-01 08:00:00',
        backtest_end_time='2020-11-10 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=10000000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)

