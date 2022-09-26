# coding=utf-8
from __future__ import print_function, absolute_import
from gm.api import *
import execjs
import requests
import json
import re
from urllib.parse import urlencode
import datetime
import numpy as np

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

        
def Get_stock(black_stock):  
    stocks = []
    url = 'https://api.heheapp.com/api/users_spool?name=pool-7'
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
    log(level='info', msg='获取低吸股票列表:{}'.format(stocks), source='strategy')
    return stocks


def get_black_stock():
    black_stock = []
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
    

    context.frash_stock = 0
    add_parameter(key='frash_stock', value=context.frash_stock, min=0, max=10, name='刷新股池', intro='刷新股池', group='刷新',
                  readonly=False)

    # algo_2(context)
    # algo_1(context)

    # schedule(schedule_func=algo_2, date_rule='1d', time_rule='9:10:00')
    schedule(schedule_func=algo_1, date_rule='1d', time_rule='9:30:00')
    schedule(schedule_func=stop_unsubscribe, date_rule='1d', time_rule='15:00:00')

def stop_unsubscribe(context):
    unsubscribe(symbols=context.stocks, frequency='tick')

def algo_2(context):
    context.stocks_close = {}
    context.stocks_deal = {}
    context.stocks = []
    context.black_stock = []
    context.stock_low = {}


def algo_1(context):
    algo_2(context)
    context.black_stock = get_black_stock()

    context.stocks = Get_stock(context.black_stock)

    context.instrument = get_instruments(symbols=context.stocks, df=True, fields='symbol, upper_limit, pre_close')

    for stock in context.stocks:
        end_date = datetime.date.today() + datetime.timedelta(days=-1)
        history_n_data = history_n(symbol=stock, frequency='1d', count=9, end_time=end_date, fields='symbol, close, low, high',
                                   adjust=ADJUST_PREV, df=True)
        data = history_n_data.close.tolist()
        data.append(0)
        context.stocks_close[stock] = data

        history_n_data = history_n(symbol=stock, frequency='1d', count=4, end_time=end_date, fields='symbol, close, low, high',
                                   adjust=ADJUST_PREV, df=True)

        history_low = min(history_n_data[history_n_data.close == history_n_data.high].low)

    context.cash_nav = context.account().cash['nav']

    subscribe(symbols=context.stocks, frequency='tick', count=5, wait_group=True, wait_group_timeout='6s',
              unsubscribe_previous=True)
 
def on_tick(context, tick):

    pos = context.account().position(symbol=tick.symbol, side=PositionSide_Long)

    if tick.symbol not in context.stocks_deal.keys():
        context.stocks_deal[tick.symbol] = [0, 0, 0, 0, 0, 0]
    if tick.symbol not in context.stock_low.keys():
        context.stock_low[tick.symbol] = tick.low
    elif tick.low < context.stock_low[tick.symbol]:
        context.stock_low[tick.symbol] = tick.low
        context.stocks_deal[tick.symbol] = [0, 0, 0, 0, 0, 0]
    

    upper_limit = context.instrument[context.instrument['symbol'] == tick.symbol].upper_limit.values[0]
    pre_close = context.instrument[context.instrument['symbol'] == tick.symbol].pre_close.values[0]

    
    amount = pos.amount if pos is not None else 0

    if amount / context.cash_nav < 0.35 and tick.price > pre_close:

        
        
        if tick.price > tick.low * 1.0191 and context.stocks_deal[tick.symbol][0] == 0:
            order_percent(symbol=tick.symbol, percent=0.05, side=OrderSide_Buy, order_type=OrderType_Limit, position_effect=PositionEffect_Open, price=upper_limit)
            log(level='info', msg='{}, 涨幅达到1.91%，买入'.format(tick.symbol), source='strategy')
            context.stocks_deal[tick.symbol][0] = 1

        if tick.price > tick.low * 1.0382 and context.stocks_deal[tick.symbol][1] == 0:
            order_percent(symbol=tick.symbol, percent=0.05, side=OrderSide_Buy, order_type=OrderType_Limit, position_effect=PositionEffect_Open, price=upper_limit)
            log(level='info', msg='{}, 涨幅达到3.82%，买入'.format(tick.symbol), source='strategy')
            context.stocks_deal[tick.symbol][1] = 1
    
        if tick.price > tick.low * 1.05 and context.stocks_deal[tick.symbol][2] == 0:
            order_percent(symbol=tick.symbol, percent=0.05, side=OrderSide_Buy, order_type=OrderType_Limit, position_effect=PositionEffect_Open, price=upper_limit)
            log(level='info', msg='{}, 涨幅达到5%，买入'.format(tick.symbol), source='strategy')
            context.stocks_deal[tick.symbol][2] = 1

        if tick.price > tick.low * 1.0618 and context.stocks_deal[tick.symbol][3] == 0:
            order_percent(symbol=tick.symbol, percent=0.05, side=OrderSide_Buy, order_type=OrderType_Limit, position_effect=PositionEffect_Open, price=upper_limit)
            log(level='info', msg='{}, 涨幅达到6.18%，买入'.format(tick.symbol), source='strategy')
            context.stocks_deal[tick.symbol][3] = 1

        if tick.price > tick.low * 1.0809 and context.stocks_deal[tick.symbol][4] == 0:
            order_percent(symbol=tick.symbol, percent=0.05, side=OrderSide_Buy, order_type=OrderType_Limit, position_effect=PositionEffect_Open, price=upper_limit)
            log(level='info', msg='{}, 涨幅达到8.09%，买入'.format(tick.symbol), source='strategy')
            context.stocks_deal[tick.symbol][4] = 1

        if tick.price == upper_limit and context.stocks_deal[tick.symbol][5] == 0:
            order_percent(symbol=tick.symbol, percent=0.05, side=OrderSide_Buy, order_type=OrderType_Limit, position_effect=PositionEffect_Open, price=upper_limit)
            log(level='info', msg='{}, 涨停，买入'.format(tick.symbol), source='strategy')
            context.stocks_deal[tick.symbol][5] = 1

        # if tick.price / avg > 1.02 and context.stocks_deal[tick.symbol][5] == 0:
        #     order_percent(symbol=tick.symbol, percent=0.05, side=OrderSide_Buy, order_type=OrderType_Limit, position_effect=PositionEffect_Open, price=upper_limit)
        #     log(level='info', msg='{}, 偏离均线2%，买入'.format(tick.symbol), source='strategy')
        #     context.stocks_deal[tick.symbol][3] = 1
    

def on_error(context, code, info):
    log(level='warning', msg='code:{}, info:{}'.format(code, info), source='strategy')

def on_execution_report(context, execrpt):

    log(level='info', msg='{}, 成交了'.format(execrpt.symbol), source='strategy')
    log(level='info', msg='成交回执:{}'.format(execrpt), source='strategy')

def on_order_status(context, order):
    
    if '资金不足' in order['ord_rej_reason_detail']:
        unsubscribe(symbols=order.symbol, frequency='tick')
        log(level='info', msg='资金不足，订阅取消', source='strategy')

def on_parameter(context, parameter):

    if parameter['name'] == '刷新股池' and parameter['value'] != context.frash_stock:

        log(level='info', msg='刷新股池', source='strategy')

        context.frash_stock = parameter['value'] 
        set_parameter(key='frash_stock', value=context.frash_stock, min=0, max=1000, name='刷新股池', intro='刷新股池', group='刷新', readonly=False)

        unsubscribe(symbols=context.stocks, frequency='tick')

        context.stocks = []
        context.stocks = Get_stock(context.black_stock)

        context.instrument = get_instruments(symbols=context.stocks, df=True, fields='symbol, upper_limit')

        for stock in context.stocks:
            end_date = datetime.date.today() + datetime.timedelta(days=-1)
            history_n_data = history_n(symbol=stock, frequency='1d', count=9, end_time=end_date, fields='symbol, close',
                                    adjust=ADJUST_PREV, df=True)
            data = history_n_data.close.tolist()
            data.append(0)
            context.stocks_close[stock] = data

        subscribe(symbols=context.stocks, frequency='tick', count=5, wait_group=True, wait_group_timeout='6s',
            unsubscribe_previous=True)

        

        

    
    

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

