import fixapp
import argparse
import logging
import quickfix as fix
from fixapp import (FixDecoder, parse_fix_options, print0,printv,printvv,printvvv)
from fixapp import BaseFixClient as FixClient
import datetime as dt
import time
import random
# from utils import *
class Session(object):
    def __init__(self,args):
        self.args         = args
        self.config_file  = args.config
        self.settings     = fix.SessionSettings(self.config_file)
        self.app          = FixClient()
        self.storeFactory = fix.FileStoreFactory(self.settings)
        self.logFactory   = fix.FileLogFactory(self.settings)
        self.initiator    = fix.SocketInitiator(self.app,self.storeFactory,self.settings,self.logFactory)

def trading_vol(order_dict):
    vol_dict={'MSFT':0,'AAPL':0,'BAC':0}
    list_id=list(order_dict) 
    for id in list_id:
        vol_dict[order_dict[id][55]]+=int(order_dict[id][38])
    print("total trading volume",vol_dict)
    
# setting_dict={'SenderCompID':"OPS_CANDIDATE_3_8639",'TargetCompID':"DTL",'SocketConnectPort':5100,'SocketConnectHost':"fix.dytechlab.com"}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FIX Client')
    parser.add_argument('--config', default='configs/fix/DTL.cfg',type=str, help='Name of configuration file')
    args = parser.parse_args()

    #-==========================================================================

 
    logging.basicConfig(level=logging.DEBUG,format='%(message)s')#logging.ERROR,logging.WARNING,logging.INFO, logging.DEBUG
    random_list=[0,1,2,3,4,5,6,7,8,9,10,11]
    try:
        app = Session(args) 
        app.initiator.start()
        # reset sequence when logon 
        time.sleep(3)
        # app.app.resetSeqLogOn()


        #### REQUIREMENT 9^th

        _, o1 = parse_fix_options("  -54 1 -55 MSFT -40 1 -44 1.9 -38 10") # Limit order
        _, o2 = parse_fix_options("  -54 2 -55 MSFT -40 2 -44 1.9 -38 10") # Limit order
        _, o3 = parse_fix_options("  -54 1 -55 MSFT -40 1  -38 10") #Market order, no price
        _, o4 = parse_fix_options("  -54 2 -55 MSFT -40 1  -38 10") #Market order, no price

        _, o5 = parse_fix_options("  -54 1 -55 AAPL -40 1 -44 1.9 -38 10") # Limit order
        _, o6 = parse_fix_options("  -54 2 -55 AAPL -40 2 -44 1.9 -38 10") # Limit order
        _, o7 = parse_fix_options("  -54 1 -55 AAPL -40 1  -38 10") #Market order, no price
        _, o8 = parse_fix_options("  -54 2 -55 AAPL -40 1  -38 10") #Market order, no price

        _, o9 = parse_fix_options("  -54 1 -55 AAPL -40 1 -44 1.9 -38 10") # Limit order
        _, o10 = parse_fix_options("  -54 2 -55 AAPL -40 2 -44 1.9 -38 10") # Limit order
        _, o11 = parse_fix_options("  -54 1 -55 AAPL -40 1  -38 10") #Market order, no price
        _, o12 = parse_fix_options("  -54 2 -55 AAPL -40 1  -38 10") #Market order, no price


        # _, sell_options2 = parse_fix_options("  -54 2 -55 BAC -40 1  -38 10")#Short, Market order, no price

        # for SHORT order, change tag 54 to 5, but I won't list here to calculate PnL in 10^th requirement 
        # for simple, I only list these order above, not list all.
        # list_options=[buy_options1,buy_options2,sell_options1,sell_options2]
        list_options=[o1,o2,o3,o4,o5,o6,o7,o8,o9,o10,o11,o12]
        for i in range(1000):
            random_option=list_options[random.choice(random_list)]
            app.app.OneOrder(**random_option)
            # app.app.buy(**random_option)
            # app.app.sell(**sell_options)
            time.sleep(0.25) # 5min=300sec, mean that we need to successfully sent each order in about 0.3sec
            if random.choice(random_list)==1:
                app.app.cancel_order(**random_option)
        
        time.sleep(1)
        #### REQUIREMENT 10^th
        transaction_list=app.app.transaction_list
        # trans_dict={'MSFT':[[],[]],'AAPL':[[None,None],[None,None]],'BAC':[[None,None],[None,None]]}
        trans_dict={'MSFT':[[],[]],'AAPL':[[],[]],'BAC':[[],[]]}
        # for a symbol:
            # [[all buy transaction],[all sell transaction]],total bought vol, total sold vol, average
# each symbol contain [total bought volume, total sold volume, bought trade vol, sold trade vol ]
        
        for trans in transaction_list:
            trans_dict[trans['Symbol']][int(trans['Side'])-1].append([trans['LastShares'],trans['LastPx']])
        import numpy as np
        
        PnL_all=0
        trading_vol_in_USD=0
        # print(transaction_list)
        for symbol in ['MSFT','AAPL','BAC']:
            PnL=0.0
            buy_trans=np.array(trans_dict[symbol][0])
            if len(buy_trans)==0:
                total_vol_buy=0.0
                total_buy_value=0.0
                avg_buy_price=0.0
            else:
                total_vol_buy=np.sum(buy_trans[:,0],axis=0)
                total_buy_value=buy_trans[:,0]@buy_trans[:,1] #multily by numpy arr will faster than seperated multiply in for loop
                avg_buy_price=total_buy_value/total_vol_buy #this number is also VWAP for buy side
                print("buy average price of {}: {} USD".format(symbol,avg_buy_price))
            sell_trans=np.array(trans_dict[symbol][1])
            if len(sell_trans)==0:
                total_vol_sell=0.0
                total_sell_value=0.0
                avg_sell_price=0.0
            else:
                total_vol_sell=np.sum(sell_trans[:,0],axis=0)
                total_sell_value=sell_trans[:,0]@sell_trans[:,1] 
                avg_sell_price=total_sell_value/total_vol_sell#this number is also VWAP for sell side
                print("sell average price of {}: {} USD".format(symbol,avg_sell_price))
            # import pdb;pdb.set_trace()
            PnL +=(avg_sell_price-avg_buy_price)*min(total_buy_value,total_sell_value) 
            PnL_all+=PnL
            # I use absolute value here because these orders are random, so we can't assure that the buy vol alway greater than the sell vol
            #vwap of the remaining stock 
            # vwap=(total_sell_value)
            trading_vol_in_USD+=total_buy_value+total_sell_value
            print("total trading volume of {}:{} USD".format(symbol,total_buy_value+total_sell_value))
            if PnL>=0:
                print("profit of trading on {}: {} USD".format(symbol,PnL))
            else:
                print("loss of trading on {}: {} USD".format(symbol,-1*PnL))
            
            
            # trading_vol_in_USD+=float(trans['LastPx'])*float(trans['LastShares'])


        print("total trading volume of this session:{} USD".format(trading_vol_in_USD))
        if PnL_all>=0:
            print("profit of trading on {}: {} USD".format(symbol,PnL_all))
        else:
            print("loss of trading on {}: {} USD".format(symbol,-1*PnL_all))
        app.initiator.stop()
        
    except (fix.ConfigError , fix.RuntimeError) as e:
        print(e)
