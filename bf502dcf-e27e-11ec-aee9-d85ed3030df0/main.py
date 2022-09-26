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

def frash_first_stock(context):
    url = 'https://api.heheapp.com/api/users_spool_weicai?name=pool-1&' + urlencode(
        {"query": "10个交易日的区间平均成交额>3亿元，上个交易日未张停，上上个交易日未涨停，非创业板，上个交易日ma3大于ma10，近20日涨幅小于50，竞价涨幅小于7%，价格小于70，可转债取反，主板， -5<=(上个交易日最低价-上个交易日MA5)/上个交易日MA5*100<=1，上个交易日实体≤5%"})
    res = requests.put(headers=headers, url=url)
    res.enconding = "utf-8"
    suc = json.loads(res.text)
    if suc['success']:
        log(level='info', msg='刷新首板票池成功', source='strategy')


def frash_black_stock(context):

    # url = 'https://api.heheapp.com/api/users_black_list?' + urlencode({"query":"煤炭||证券||银行||融资方式包含可转债"})
    url = 'https://api.heheapp.com/api/users_black_list_weicai?' + urlencode({"query":"10个交易日的区间日均换手率>30%||上市天数>30日取反||煤炭||证券||银行"})
    res = requests.put(headers=headers, url=url)
    res.enconding = "utf-8"
    suc = json.loads(res.text)
    if suc['success']:
        log(level='info', msg='黑名单刷新成功！', source='strategy')


# 策略中必须有init方法
def init(context):

    algo_1(context)


    schedule(schedule_func=algo_1, date_rule='1d', time_rule='9:29:30')
    
def algo_2(context):

    # unsubscribe(symbols=context.stocks, frequency='300s')
    unsubscribe(symbols=context.stocks, frequency='tick')
    log(level='info', msg='到点了, 取消订阅了', source='strategy')


def algo_1(context):

    context.first_stocks = []
    context.black_stock = []
    while not context.first_stocks:
        frash_first_stock(context)
        context.first_stocks = Get_stock(context.first_stocks, context.black_stock)

    frash_black_stock(context)

    context.avgs = {}
    context.stocks = []

    context.avg = 3
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
        context.stocks.append(Account_position['symbol'])
        # context.avgs[Account_position['symbol']] = 0

    context.history_data = history(symbol=context.stocks, frequency='1d', start_time=last_day, end_time=last_day,
                                   fields='symbol, close', adjust=ADJUST_PREV, df=True)
    context.instrument = get_instruments(symbols=context.stocks, df=True, fields='symbol, lower_limit')

    # subscribe(context.stocks, frequency='300s', count=context.count, wait_group=False, wait_group_timeout='10s',
    #           unsubscribe_previous=False)

    subscribe(context.stocks, frequency='tick', count=context.count, wait_group=False, wait_group_timeout='10s',
              unsubscribe_previous=False)

    log(level='info', msg='目前持仓:{}'.format(context.stocks), source='strategy')

    schedule(schedule_func=algo_2, date_rule='1d', time_rule='14:56:30')


# def on_bar(context, bars):
#     for bar in bars:
#         # 获取通过subscribe订阅的数据
#         prices = context.data(bar.symbol, '300s', context.count, fields='close')

#         #计算MA
#         context.avgs[bar.symbol] = talib.SMA(prices.values.reshape(context.count), context.avg)[-1] * 0.998

    

def on_tick(context, tick):

    high = context.data(tick.symbol, 'tick', context.count, fields='high')[0].high
    pos = context.account().position(symbol=tick.symbol, side=PositionSide_Long)


    close = context.history_data[context.history_data['symbol'] == tick.symbol].close.values[0]
    low_limit = context.instrument[context.instrument['symbol'] == tick.symbol].lower_limit.values[0]

    now = context.now.timetz()

    # if pos and pos.available_now > 0 and tick.low != 0 and  high != 0:  # 有持仓就跌停价卖出股票。
    
    if pos and pos.available_now > 0 and tick.low != 0 and context.still == 1: 

        # if pos.price / pos.vwap < 0.7:

        #     order_volume(symbol=tick.symbol, volume=pos.available_now, side=OrderSide_Sell , order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)
        #     log(level='info', msg='{}, 止损了'.format(tick.symbol), source='strategy')



        # if pos.price < context.avgs[tick.symbol]:

        #     order_volume(symbol=tick.symbol, volume=pos.available_now, side=OrderSide_Sell , order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)
        #     log(level='info', msg='{}, 破均线了'.format(tick.symbol), source='strategy')


        if pos.price < tick.open * 0.98 and pos.price < low_limit * 1.005 and context.nuclear_button == 1:

            order_volume(symbol=tick.symbol, volume=pos.available_now, side=OrderSide_Sell, order_type=OrderType_Limit,
                         position_effect=PositionEffect_Close, price=low_limit)
            log(level='info', msg='{}, 止损'.format(tick.symbol), source='strategy')


        elif (pos.price / tick.low >= 1.06 and tick.low >= close) or (
                pos.price / tick.low >= 1.045 and tick.low < close):
            order_volume(symbol=tick.symbol, volume=pos.available_now, side=OrderSide_Sell,
                            order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)
            log(level='info', msg='{}, 冲高止盈了'.format(tick.symbol), source='strategy')
                

        # elif pos.price / high < 0.985:

        #     order_volume(symbol=tick.symbol, volume=pos.available_now, side=OrderSide_Sell , order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)
        #     log(level='info', msg='{}, 回落止盈了'.format(tick.symbol), source='strategy')

        elif tick.quotes[0]['bid_v'] * tick.quotes[0]['bid_p'] < 10000000 and tick.quotes[0]['ask_p'] == 0:

            order_volume(symbol=tick.symbol, volume=pos.available_now, side=OrderSide_Sell, order_type=OrderType_Limit,
                         position_effect=PositionEffect_Close, price=low_limit)
            log(level='info', msg='{}, 炸板了'.format(tick.symbol), source='strategy')

        elif now > datetime.time(14, 55, 00) and tick.quotes[0]['ask_p'] != 0:

            order_volume(symbol=tick.symbol, volume=pos.available_now, side=OrderSide_Sell , order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)
            log(level='info', msg='{}, 到点清仓了'.format(tick.symbol), source='strategy')

        # elif now > datetime.time(9, 32, 00) and pos.price < tick.open:
        #     order_volume(symbol=tick.symbol, volume=pos.available_now, side=OrderSide_Sell , order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)
        #     log(level='info', msg='{}, 9:32之后还在水下，卖出'.format(tick.symbol), source='strategy')

    # else:

        
        # unsubscribe(symbols=tick.symbol, frequency='300s')
        # unsubscribe(symbols=tick.symbol, frequency='tick')
        # log(level='info', msg='{}, 没可交易票数, 取消订阅了'.format(tick.symbol), source='strategy')


def on_execution_report(context, execrpt):
    # unsubscribe(symbols=execrpt.symbol, frequency='300s')
    # unsubscribe(symbols=execrpt.symbol, frequency='tick')

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

