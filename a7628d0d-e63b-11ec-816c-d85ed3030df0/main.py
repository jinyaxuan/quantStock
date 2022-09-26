# coding=utf-8
# coding=utf-8
from __future__ import print_function, absolute_import
from gm.api import *
import talib
import datetime



# 策略中必须有init方法
def init(context):

    algo_1(context)

    context.nuclear_button = 1
    add_parameter(key='nuclear_button', value=context.nuclear_button, min=0, max=1, name='核按钮', intro='核按钮开关',
                  group='打板', readonly=False)

    schedule(schedule_func=algo_1, date_rule='1d', time_rule='9:30:00')
    
def algo_2(context):

    # unsubscribe(symbols=context.stocks, frequency='300s')
    unsubscribe(symbols=context.stocks, frequency='tick')
    log(level='info', msg='到点了, 取消订阅了', source='strategy')


def algo_1(context):

    context.avgs = {}
    context.stocks = []

    context.avg = 3
    context.count = 20
    last_day = get_previous_trading_date(exchange='SHSE', date=context.now) 

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

    if pos and pos.available_now > 0 and tick.low != 0 and  high != 0:  # 有持仓就跌停价卖出股票。

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
                

        elif pos.price / high < 0.985:

            order_volume(symbol=tick.symbol, volume=pos.available_now, side=OrderSide_Sell , order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)
            log(level='info', msg='{}, 回落止盈了'.format(tick.symbol), source='strategy')

        elif tick.quotes[0]['bid_v'] * tick.quotes[0]['bid_p'] < 10000000 and tick.quotes[0]['ask_p'] == 0:

            order_volume(symbol=tick.symbol, volume=pos.available_now, side=OrderSide_Sell, order_type=OrderType_Limit,
                         position_effect=PositionEffect_Close, price=low_limit)
            log(level='info', msg='{}, 炸板了'.format(tick.symbol), source='strategy')

        elif now == datetime.time(14, 55, 00) and tick.quotes[0]['ask_p'] != 0:

            order_volume(symbol=tick.symbol, volume=pos.available_now, side=OrderSide_Sell , order_type=OrderType_Limit, position_effect=PositionEffect_Close, price=low_limit)
            log(level='info', msg='{}, 到点清仓了'.format(tick.symbol), source='strategy')

    # else:

        
    #     # unsubscribe(symbols=tick.symbol, frequency='300s')
    #     unsubscribe(symbols=tick.symbol, frequency='tick')
    #     log(level='info', msg='{}, 没可交易票数, 取消订阅了'.format(tick.symbol), source='strategy')


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

