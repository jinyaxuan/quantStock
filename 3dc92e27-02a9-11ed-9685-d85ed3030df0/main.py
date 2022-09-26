# coding=utf-8
# coding=utf-8
from __future__ import print_function, absolute_import
from gm.api import *
import talib
import datetime
from urllib.parse import urlencode
import requests
import json

headers ={
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding":"gzip, deflate, br",
    "Accept-Language":"zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "authorization":"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJOVGswTVE9PSIsImV4cCI6MTY2MjgxOTkxOH0.NrSmRLAMyUHQnS8eJERak9eecB8KaSeHhhdy7-3BTB8",
    "Connection":"keep-alive",
    "origin": "https://www.heheapp.com",
    "Referer": "https://www.heheapp.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.81 Safari/537.36 Edg/104.0.1293.54"
    }  


def Get_stock(black_stock):  
    stocks = []
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

def frash_first_stock(context):
    url = 'https://api.heheapp.com/api/users_spool_weicai?name=pool-1&' + urlencode(
        {"query": "上个交易日到前10个交易日的区间平均成交额>3亿元，上个交易日未张停，上个交易日曾涨停取反，上上个交易日未涨停，非创业板，上个交易日ma3大于ma10，近20日涨幅小于50，竞价涨幅小于7%，可转债取反，主板，1%<上个交易日实体≤5% ，上个交易日ma10大于ma20，上个交易日振幅小于9%，今日涨停价>上个交易日90%成本上限，剔除上个交易日竞价抢筹"})
    res = requests.put(headers=headers, url=url)
    res.enconding = "utf-8"
    suc = json.loads(res.text)
    if suc['success']:
        log(level='info', msg='刷新首板票池成功', source='strategy')


def frash_black_stock():

    url = 'https://api.heheapp.com/api/users_black_list_weicai?' + urlencode({"query":"10个交易日的区间日均换手率>30%||上市天数>30日取反||煤炭||证券||银行"})
    res = requests.put(headers=headers, url=url)
    res.enconding = "utf-8"
    # suc = json.loads(res.text)
    # if suc['success']:
    log(level='info', msg='黑名单刷新成功！', source='strategy')


# 策略中必须有init方法
def init(context):

    # algo_3(context)
    # algo_1(context)


    schedule(schedule_func=algo_1, date_rule='1d', time_rule='9:30:00')
    schedule(schedule_func=algo_3, date_rule='1d', time_rule='9:27:00')
    
def algo_2(context):

    # unsubscribe(symbols=context.stocks, frequency='300s')
    unsubscribe(symbols=list(context.stocks.keys()), frequency='tick')
    log(level='info', msg='到点了, 取消订阅了', source='strategy')

def algo_3(context):
    frash_black_stock()
    context.first_stocks = []
    context.black_stock = []
    while not context.first_stocks:
        frash_first_stock(context)
        context.first_stocks = Get_stock(context.black_stock)

    


def algo_1(context):
    

    context.stocks = {}
    context.sell = {}

    context.count = 20
    last_day = get_previous_trading_date(exchange='SHSE', date=context.now) 

    context.nuclear_button = 1
    add_parameter(key='nuclear_button', value=context.nuclear_button, min=0, max=1, name='核按钮', intro='核按钮开关',
                  group='打板', readonly=False)

    context.still = 1
    add_parameter(key='still', value=context.still, min=0, max=1, name='交易开关', intro='交易开关',
                group='打板', readonly=False)

    # 所有持仓
    Account_positions = context.account().positions()

    for Account_position in Account_positions:
        context.stocks[Account_position['symbol']] = 1.0
        context.sell[Account_position['symbol']] = [0, 0, 0, 10000]


    for key in context.stocks.keys():
        add_parameter(key=key, value=context.stocks[key], min=0, max=1, name='{}'.format(key), intro='{}仓位'.format(key),
            group='仓位', readonly=False)

    context.history_data = history(symbol=list(context.stocks.keys()), frequency='1d', start_time=last_day, end_time=last_day,
                                   fields='symbol, close', adjust=ADJUST_PREV, df=True)
    
    context.instrument = get_instruments(symbols=list(context.stocks.keys()), df=True, fields='symbol, lower_limit')

    subscribe(list(context.stocks.keys()), frequency='tick', count=context.count, wait_group=False, wait_group_timeout='10s',
              unsubscribe_previous=False)

    log(level='info', msg='目前持仓:{}'.format(list(context.stocks.keys())), source='strategy')

    schedule(schedule_func=algo_2, date_rule='1d', time_rule='14:56:30')
    

def on_tick(context, tick):

    pos = context.account().position(symbol=tick.symbol, side=PositionSide_Long)


    close = context.history_data[context.history_data['symbol'] == tick.symbol].close.values[0]
    low_limit = context.instrument[context.instrument['symbol'] == tick.symbol].lower_limit.values[0]
    avg = tick.cum_amount / tick.cum_volume

    now = context.now.timetz()
    
    if pos and pos.available_now > 0 and tick.low != 0 and context.still == 1 and context.stocks[tick.symbol] > 0: 


        # if pos.price < tick.open * 0.98 and pos.price < low_limit * 1.005 and context.nuclear_button == 1:

        #     order_volume(symbol=tick.symbol, volume=pos.available_now, side=OrderSide_Sell, order_type=OrderType_Limit,
        #                  position_effect=PositionEffect_Close, price=low_limit)
        #     log(level='info', msg='{}, 止损'.format(tick.symbol), source='strategy')

        # elif (pos.price / tick.low >= 1.06 and tick.price >= close) or (
        #         pos.price / tick.low >= 1.045 and tick.price < close):
        if context.sell[tick.symbol][-1] < tick.low:
            context.sell[tick.symbol][-1] = tick.low
            context.sell[tick.symbol][0] = 0
            
        if pos.price / avg >= 1.025 and context.sell[tick.symbol][0] == 0 and context.stocks[tick.symbol] > 0:

            order_volume(symbol=tick.symbol, volume=int(pos.available_now * context.stocks[tick.symbol] // 100 * 100 // 4), side=OrderSide_Sell,
                            order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)

            log(level='info', msg='{}, 偏离均线2.5%，减1/4仓'.format(tick.symbol), source='strategy')
            context.stocks[tick.symbol] = 0
            context.sell[tick.symbol][0] = 1
        
        elif pos.price / tick.low >= 1.035 and context.sell[tick.symbol][0] == 0 and context.stocks[tick.symbol] > 0:

            order_volume(symbol=tick.symbol, volume=int(pos.available_now * context.stocks[tick.symbol] // 100 * 100 // 4), side=OrderSide_Sell,
                            order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)

            log(level='info', msg='{}, 冲高3.5%，减1/4仓'.format(tick.symbol), source='strategy')
            context.stocks[tick.symb8ol] = 0
            context.sell[tick.symbol][0] = 1

        elif pos.price / avg >= 1.035 and context.sell[tick.symbol][1] == 0 and context.stocks[tick.symbol] > 0:

            order_volume(symbol=tick.symbol, volume=int(pos.available_now * context.stocks[tick.symbol] // 100 * 100 // 2), side=OrderSide_Sell,
                            order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)

            log(level='info', msg='{}, 偏离均线3.5%，减半仓'.format(tick.symbol), source='strategy')
            context.stocks[tick.symbol] = 0
            context.sell[tick.symbol][1] = 1
        
        elif pos.price / tick.low >= 1.055 and context.sell[tick.symbol][2] == 0 and context.stocks[tick.symbol] > 0:

            order_volume(symbol=tick.symbol, volume=int(pos.available_now * context.stocks[tick.symbol] // 100 * 100 // 2), side=OrderSide_Sell,
                            order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)

            log(level='info', msg='{}, 冲高5.5%，减半仓'.format(tick.symbol), source='strategy')
            context.stocks[tick.symb8ol] = 0
            context.sell[tick.symbol][1] = 1

        elif pos.price / avg >= 1.045 and context.sell[tick.symbol][2] == 0 and context.stocks[tick.symbol] > 0:

            order_volume(symbol=tick.symbol, volume=int(pos.available_now * context.stocks[tick.symbol] // 100 * 100), side=OrderSide_Sell,
                            order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)

            log(level='info', msg='{}, 偏离均线4.5%，清仓'.format(tick.symbol), source='strategy')
            context.stocks[tick.symbol] = 0
            context.sell[tick.symbol][2] = 1

        elif pos.price / tick.low >= 1.075 and context.sell[tick.symbol][2] == 0 and context.stocks[tick.symbol] > 0:

            order_volume(symbol=tick.symbol, volume=int(pos.available_now * context.stocks[tick.symbol] // 100 * 100), side=OrderSide_Sell,
                            order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)

            log(level='info', msg='{}, 冲高7.5%，清仓'.format(tick.symbol), source='strategy')
            context.stocks[tick.symbol] = 0
            context.sell[tick.symbol][2] = 1
                
        elif tick.quotes[0]['bid_v'] * tick.quotes[0]['bid_p'] < 10000000 and tick.quotes[0]['ask_p'] == 0:

            order_volume(symbol=tick.symbol, volume=pos.available_now, side=OrderSide_Sell, order_type=OrderType_Limit,
                         position_effect=PositionEffect_Close, price=low_limit)
            log(level='info', msg='{}, 炸板了'.format(tick.symbol), source='strategy')
        
        # elif now > datetime.time(10, 00, 00) and pos.price / close < 0.96 and tick.quotes[0]['ask_p'] != 0:

        #     order_volume(symbol=tick.symbol, volume=int(pos.available_now * context.stocks[tick.symbol] // 100 * 100), side=OrderSide_Sell , order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)
        #     log(level='info', msg='{}, 十点之后涨幅小于-4%，割肉了'.format(tick.symbol), source='strategy')
        #     context.stocks[tick.symbol] = 0

        # elif now > datetime.time(14, 55, 00) and tick.quotes[0]['ask_p'] != 0:

        #     order_volume(symbol=tick.symbol, volume=int(pos.available_now * context.stocks[tick.symbol] // 100 * 100), side=OrderSide_Sell , order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)
        #     log(level='info', msg='{}, 到点清仓了'.format(tick.symbol), source='strategy')
        #     context.stocks[tick.symbol] = 0


def on_execution_report(context, execrpt):

    log(level='info', msg='{}, 交易成功'.format(execrpt.symbol), source='strategy')
    log(level='info', msg='回执信息:{}'.format(execrpt), source='strategy')


def on_parameter(context, parameter):
    if parameter['name'] == '核按钮' and parameter['value'] != context.nuclear_button:
        nuclear = {0: '关闭', 1: '启动'}

        context.nuclear_button = parameter['value']
        set_parameter(key='nuclear_button', value=context.nuclear_button, min=0, max=1, name='核按钮', intro='核按钮开关',
                      group='打板', readonly=False)
        log(level='info', msg='核按钮:{}'.format(nuclear[context.nuclear_button]), source='strategy')

    
    elif parameter['name'] == '交易开关' and parameter['value'] != context.still:
        nuclear = {0: '关闭', 1: '启动'}

        context.still = parameter['value']
        set_parameter(key='still', value=context.still, min=0, max=1, name='交易开关', intro='交易开关',
                      group='打板', readonly=False)
        log(level='info', msg='交易开关:{}'.format(nuclear[context.still]), source='strategy')


    elif parameter['name'] in context.stocks.keys():
        if parameter['value'] != context.stocks[parameter['name']]:

            context.stocks[parameter['name']] = parameter['value']
            set_parameter(key=parameter['name'], value=context.stocks[parameter['name']], min=0, max=1, name='{}'.format(parameter['name']), intro='{}仓位'.format(parameter['name']),
                group='仓位', readonly=False)

            log(level='info', msg='{}的卖出仓位为:{}'.format(parameter['name'], context.stocks[parameter['name']]), source='strategy')


def on_error(context, code, info):
    print('code:{}, info:{}'.format(code, info))


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
    run(strategy_id='57ea1522-dbd0-11ec-9dd6-d85ed3030def',
        filename='main.py',
        mode=MODE_BACKTEST,
        token='7cf27f5eeede68e0ffefdd86071886bcf11258bb',
        backtest_start_time='2020-11-01 08:00:00',
        backtest_end_time='2020-11-10 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=10000000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)

