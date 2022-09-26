# coding=utf-8
from __future__ import print_function, absolute_import
from gm.api import *

import datetime


# 策略中必须有init方法
def init(context):
    end_date = datetime.date.today()
    # start_date = end_date - datetime.timedelta(days = 3)
    # print(end_date)
    history_n_data = history_n(symbol='SHSE.600992', frequency='1d', count=4, end_time=end_date, fields='symbol, close, low, high',
                                   adjust=ADJUST_PREV, df=True)

    min(history_n_data[history_n_data.close == history_n_data.high].low)
    


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
    run(strategy_id='157505e2-f46e-11ec-a9e9-d85ed3030df0',
        filename='main.py',
        mode=MODE_BACKTEST,
        token='f6ab156e8a096afef63fe107d268d05b237e0d1a', 
        backtest_start_time='2020-11-09 08:00:00',
        backtest_end_time='2020-11-10 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=10000000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)

