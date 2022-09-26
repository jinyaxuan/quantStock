# coding=utf-8
from __future__ import print_function, absolute_import
from gm.api import *

import pandas as pd


# 策略中必须有init方法
def init(context):

    history_data = history(symbol='SHSE.000300', frequency='1d', start_time='2022-02-01', 
     end_time='2022-05-20', fields='symbol, open, close, low, high, cum_volume,', adjust=ADJUST_PREV, df= True)
    history_instruments = get_history_instruments(symbols='SZSE.000736', start_date='2022-02-01', end_date='2022-05-20', fields='symbol, upper_limit', df=True)

    data = pd.merge(history_data, history_instruments, on='symbol')
    
    print(data.head())


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
    run(strategy_id='dee13108-e719-11ec-bb87-d85ed3030df0',
        filename='main.py',
        mode=MODE_BACKTEST,
        token='f6ab156e8a096afef63fe107d268d05b237e0d1a',
        backtest_start_time='2020-11-01 08:00:00',
        backtest_end_time='2020-11-10 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=10000000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)

