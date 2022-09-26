# coding=utf-8
from __future__ import print_function, absolute_import
from gm.api import *
import execjs
import requests
import json
import re
from urllib.parse import urlencode

headers ={
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding":"gzip, deflate, br",
        "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "authorization":"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJOVGswTVE9PSIsImV4cCI6MTY2MjgxOTkxOH0.NrSmRLAMyUHQnS8eJERak9eecB8KaSeHhhdy7-3BTB8",
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

def frash_first_stock():
    url = 'https://api.heheapp.com/api/users_spool_weicai?name=pool-1&' + urlencode(
        {"query": "10个交易日的区间平均成交额>4亿元，1天前未张停，2天前未涨停，非创业板，上个交易日ma3大于ma10，前10日涨幅小于50，竞价涨幅小于7%，价格小于70"})
    res = requests.put(headers=headers, url=url)
    res.enconding = "utf-8"
    suc = json.loads(res.text)
    if suc['success']:
        log(level='info', msg='刷新首板票池成功', source='strategy')

def get_more_stock(more_stocks, black_stock):

    url = 'https://api.heheapp.com/api/users_spool?name=default'
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
            more_stocks.append(stock)
    log(level='info', msg='获取连板股票列表:{}'.format(more_stocks), source='strategy')
    return more_stocks

def frash_more_stock():
    url = 'https://api.heheapp.com/api/users_spool_weicai?name=default&' + urlencode({"query":"上个交易日ma3角度大于60，上个交易日ma30角度大于10，上个交易日ma5大于ma30，主板，非st，上个交易日涨停，上个交易日封板金额大于3000万，今日9:25竞价额/上个交易日总成交额大于0.028，今日涨停价大于压力位，非60开头，上个交易日下午开板次数小于3，业绩为正，概念龙头数>=1"})
    res = requests.put(headers=headers, url=url)
    res.enconding = "utf-8"
    suc = json.loads(res.text)
    if suc['success']:
        log(level='info', msg='刷新连板票池成功', source='strategy')

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

def frash_black_stock():
    # url = 'https://api.heheapp.com/api/users_black_list?' + urlencode({"query":"煤炭||证券||银行||融资方式包含可转债"})
    url = 'https://api.heheapp.com/api/users_black_list?' + urlencode({"query":"10个交易日的区间日均换手率>30%||上市天数>30日取反"})
    res = requests.put(headers=headers, url=url)
    res.enconding = "utf-8"
    suc = json.loads(res.text)
    if suc['success']:
        log(level='info', msg='黑名单刷新成功！', source='strategy')


def get_button(context):
    context.daily_limit = 15000000
    context.kill_an_order = 12000000
    add_parameter(key='daily_limit', value=context.daily_limit, min=0, max=99999999999, name='封单金额', intro='调整封单',
                  group='打板', readonly=False)
    add_parameter(key='kill_an_order', value=context.kill_an_order, min=0, max=99999999999, name='撤单金额', intro='调整撤单',
                  group='打板', readonly=False)

    context.retery = 2000000
    context.deal_time = 4
    add_parameter(key='retery', value=context.retery, min=0, max=99999999999, name='一字板回封金额', intro='调整金额', group='打板',
                  readonly=False)
    add_parameter(key='deal_time', value=context.deal_time, min=0, max=10, name='排撤次数', intro='调整次数', group='打板',
                  readonly=False)

    context.frash_stock = 0
    add_parameter(key='frash_stock', value=context.frash_stock, min=0, max=10, name='刷新股池', intro='刷新股池', group='刷新',
                  readonly=False)


# 策略中必须有init方法
def init(context):
    # algo_1(context)

    schedule(schedule_func=algo_1, date_rule='1d', time_rule='9:25:30')


def algo_1(context):
    context.Account_positions = [i.symbol for i in context.account().positions()]

    context.black_stock = []
    context.stocks = []
    context.more_stocks = []

    while not context.black_stock:
        frash_black_stock()
        context.black_stock = get_black_stock(context.black_stock)

    while not context.stocks:
        frash_first_stock()
        context.stocks = Get_stock(context.stocks, context.black_stock)

    # while not context.more_stocks:
    #     frash_more_stock()
    #     context.more_stocks = get_more_stock(context.more_stocks, context.black_stock)

    context.instrument = get_instruments(symbols=context.stocks, df=True, fields='symbol, upper_limit')
    context.instrument['deal'] = 0

    get_button(context)

    subscribe(symbols=context.stocks, frequency='tick', count=5, wait_group=True, wait_group_timeout='6s',
              unsubscribe_previous=True)

    schedule(schedule_func=algo_2, date_rule='1d', time_rule='14:56:50')

def algo_2(context):
    
    order_cancel(get_unfinished_orders())
    unsubscribe(symbols=context.stocks, frequency='tick')
    log(level='info', msg='到点了，下班，全撤', source='strategy')
    
def on_tick(context, tick):

    upper_limit = context.instrument[context.instrument['symbol'] == tick.symbol].upper_limit.values[0]
    context.unfinished_orders = [i['symbol'] for i in get_unfinished_orders()]
    #获取交易状态
    deal = context.instrument[context.instrument['symbol'] == tick.symbol].deal.values[0]

    # try:

    #打板下单
    if tick.quotes[0]['ask_p'] == 0 and tick.quotes[0]['bid_v'] * tick.quotes[0]['bid_p'] > context.daily_limit and tick.symbol not in context.unfinished_orders and tick.open != upper_limit and deal <= context.deal_time:

        order_percent(symbol=tick.symbol, percent=0.15, side=OrderSide_Buy, order_type=OrderType_Limit, position_effect=PositionEffect_Open, price=upper_limit)
        log(level='info', msg='{}, 下单了'.format(tick.symbol), source='strategy')

    #回封下单
    elif tick.open == upper_limit and tick.low != upper_limit and tick.quotes[0]['ask_p'] == 0 and tick.quotes[0][
        'bid_v'] * tick.quotes[0][
        'bid_p'] > context.retery and deal <= context.deal_time and tick.symbol not in context.unfinished_orders:

        order_percent(symbol=tick.symbol, percent=0.15, side=OrderSide_Buy, order_type=OrderType_Limit,
                      position_effect=PositionEffect_Open, price=upper_limit)
        log(level='info', msg='{}, 下单了'.format(tick.symbol), source='strategy')

    #撤单
    if tick.quotes[0]['bid_v'] != 0:
        if (tick.last_volume / (tick.last_volume + tick.quotes[0]['bid_v']) > 0.13 or tick.quotes[0]['bid_v'] * tick.quotes[0]['bid_p'] < context.kill_an_order) and tick.symbol in context.unfinished_orders:

            order_cancel([i for i in get_unfinished_orders() if i['symbol'] == tick.symbol])
            context.instrument.loc[context.instrument['symbol'] == tick.symbol, 'deal'] += 1
            
            log(level='info', msg='{}, 撤单了'.format(tick.symbol), source='strategy')
            log(level='info', msg='大单砸：{}'.format(tick.last_volume / (tick.last_volume + tick.quotes[0]['bid_v'])), source='strategy')
            log(level='info', msg='剩余封单：{}'.format(tick.quotes[0]['bid_v'] * tick.quotes[0]['bid_p']), source='strategy')
    
    # except:
    #     log(level='info', msg='小问题，已跳过', source='strategy')

def on_parameter(context, parameter):

    if parameter['name'] == '封单金额' and parameter['value'] != context.daily_limit:

        context.daily_limit = parameter['value']
        set_parameter(key='daily_limit', value=context.daily_limit, min=0, max=9999999999999, name='封单金额', intro='调整封单', group='打板', readonly=False)
        log(level='info', msg='封单金额修改为:{}'.format(context.daily_limit), source='strategy')

        
    elif parameter['name'] == '撤单金额' and parameter['value'] != context.kill_an_order:

        context.kill_an_order = parameter['value'] 
        set_parameter(key='kill_an_order', value=context.kill_an_order, min=0, max=9999999999999, name='撤单金额', intro='调整撤单', group='打板', readonly=False)
        log(level='info', msg='撤单金额修改为:{}'.format(context.kill_an_order), source='strategy')

    elif parameter['name'] == '一字板回封金额' and parameter['value'] != context.retery:

        context.retery = parameter['value'] 
        set_parameter(key='retery', value=context.retery, min=0, max=99999999999, name='一字板回封金额', intro='调整金额', group='打板', readonly=False)
        log(level='info', msg='一字板回封金额修改为:{}'.format(context.retery), source='strategy')

    elif parameter['name'] == '排撤次数' and parameter['value'] != context.deal_time:

        context.deal_time = parameter['value'] 
        set_parameter(key='deal_time', value=context.deal_time, min=0, max=10, name='排撤次数', intro='调整次数', group='打板', readonly=False)
        log(level='info', msg='排撤次数修改为:{}'.format(context.deal_time), source='strategy')

    elif parameter['name'] == '刷新股池' and parameter['value'] != context.frash_stock:

        context.frash_stock = parameter['value'] 
        set_parameter(key='frash_stock', value=context.frash_stock, min=0, max=1000, name='刷新股池', intro='刷新股池', group='刷新', readonly=False)

        context.stocks = []
        frash_first_stock()
        context.stocks = Get_stock(context.stocks, context.black_stock)

        log(level='info', msg='刷新股池', source='strategy')


def on_error(context, code, info):
    log(level='warning', msg='code:{}, info:{}'.format(code, info), source='strategy')

def on_execution_report(context, execrpt):
    unsubscribe(symbols=execrpt.symbol, frequency='tick')
    context.instrument.loc[context.instrument['symbol'] == execrpt.symbol, 'deal'] = 100

    context.Account_positions = [i.symbol for i in context.account().positions()]

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

