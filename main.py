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

# setting_dict={'SenderCompID':"OPS_CANDIDATE_3_8639",'TargetCompID':"DTL",'SocketConnectPort':5100,'SocketConnectHost':"fix.dytechlab.com"}
if __name__ == '__main__':
    #check arguments from commmand line and set everything up
    parser = argparse.ArgumentParser(description='FIX Client')
    parser.add_argument('--config', type=str, help='Name of configuration file')
    args = parser.parse_args()

    #-==========================================================================

    levels = [logging.ERROR,logging.WARNING,logging.INFO, logging.DEBUG]
    level = levels[min(len(levels)-1,3)]  # get number to work with logging module

    logging.basicConfig(level=level,format='%(message)s')
    random_list=[0,1,2,3]
    try:
        app = Session(args) 
        app.initiator.start()
        # reset sequence when logon 
        time.sleep(5)
        # app.app.resetSeqLogOn()

        _, buy_options1 = parse_fix_options("  -54 1 -55 MSFT -40 2 -44 1.145 -38 100000")
        _, buy_options2 = parse_fix_options("  -54 1 -55 MSFT -40 1  -38 100000") #Market order, no price
        _, sell_options1 = parse_fix_options("  -54 2 -55 AAPL -40 2 -44 1.145 -38 100000")
        _, sell_options2 = parse_fix_options("  -54 2 -55 BAC -40 1  -38 100000")#Market order, no price
        list_options=[buy_options1,buy_options2,sell_options1,sell_options2]
        for i in range(1000):
            random_option=list_options[random.choice(random_list)]
            app.app.OneOrder(**random_option)
            # app.app.buy(**random_option)
            # app.app.sell(**sell_options)
            time.sleep(0.25) # 5min=300sec, mean that we need to successfully sent each order in 0.3sec
            if random.choice(random_list)==1:
                app.app.cancel_order(**random_option)
        
        order_dict=app.app.ORDERS_DICT
        #to be continue on require 10
    except (fix.ConfigError , fix.RuntimeError) as e:
        print(e)
