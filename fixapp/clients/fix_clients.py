__all__ = ['BaseFixClient']
#import time
import datetime as dt
import quickfix as fix 

from fixapp import FixDecoder, print0, printv, printvv, printvvv, unicode_fix


class BaseFixClient(fix.Application):
    # def __init__(self,session_settings):
    sender="OPS_CANDIDATE_3_8639"
    target="DTL"
    CurrentSeqNum=0
    
    orderID = 0
    execID  = 0
    decoder = FixDecoder()      #create a FIX decoder instance as a class varaible for the application
    session_settings = None     #a reference to the session settings object
    settingsDic = {}
    session_ids = [] 
    #Keep track of orders and IDs
    ORDERS_DICT   = {}
    LASTEST_ORDER = {}
    
    
    
    #Keep track of orders and ids
    open_subs   = []
    open_orders = []

    '''=========================================================================
    Internal message methdos
    '''


    def onCreate(self, sessionID):
        return


    def onLogon(self, sessionID):
        self.sessionID = sessionID
        print('Q:reset sequence numberson both sides ')
        # self.resetSeqLogOn()
        return


    def onLogout(self, sessionID):
        #fix.Session.lookupSession(sessionID).logout();
        return


    def toAdmin(self, message,sessionID):
        return


    def fromAdmin(self, message, sessionID):
        fix_str = unicode_fix(message.toString())
        print("\nIncoming Msg (fromAdmin):\n{}".format(fix_str))
        # printvv("\nIncoming Msg (fromAdmin):\n{}".format(fix_str))
        self.decoder.print_report(message)
        return


    def toApp(self, message, sessionID):
        fix_str = unicode_fix(message.toString())
        return

    def fromApp(self, message, sessionID):
        '''Capture Messages coming from the counterparty'''
        print("sessionID.toString)fromApp",sessionID)
        fix_str = unicode_fix(message.toString())
        self.decoder.print_report(message)
        return


    def genOrderID(self):
        self.orderID += 1
        return str(self.orderID) + '-' + str(dt.datetime.timestamp(dt.datetime.utcnow()))

    def genExecID(self):
        self.execID += 1
        return str(self.execID) + '-' + str(dt.datetime.timestamp(dt.datetime.utcnow()))
    def increase_seqnum(self):
        self.CurrentSeqNum+=1

    def _make_standard_header(self,MsgType):
        '''Make a standard header for Fortex FIX 4.4 Server based on their instruction file.
        A standard header for Fortex has the following tags (first 6 tags must be in this exact order):
        *     8  - BeginString  - required
        *     9  - BodyLength   - required
        *     35 - MsgType      - required
        *     49 - SenderCompID - required
        *     56 - TargetCompID - required
        *     34 - MsgSeqNum    - required
        *     52 - SendingTime  - required
        '''
        msg = fix.Message()
        msg.getHeader().setField(fix.BeginString(fix.BeginString_FIX42))
        # msg.getHeader().setField(fix.BeginString(fix.BeginString_FIX42))
        msg.getHeader().setField(fix.MsgType(MsgType))
        msg.getHeader().setField(fix.SenderCompID(self.sender))
        msg.getHeader().setField(fix.TargetCompID(self.target))
        msg.getHeader().setField(fix.MsgSeqNum(self.CurrentSeqNum))
        msg.getHeader().setField(fix.SendingTime(1))
        self.increase_seqnum()
        # fix_str = unicode_fix(msg.toString())
        # print("fix_str",    fix_str)
        return msg


    def get_open_orders(self):
        return self.open_orders

    def get_last_order(self):
        return self.open_orders[-1]

    def close_order(self,id):
        self.open_orders.remove(id)

    def add_order(self,id):
        self.open_orders.append(str(id))
        

    def _record_json_order(self, msg, wanted_tags=[1,40,54,38,55,167]):
        order_object = {}

        #For now I am going to store the entire message as a string
        order_object['raw_msg'] = msg.toString()

        for tag in wanted_tags:
            order_object[tag] = msg.getField(tag)

        id_tag   = 11    #tag for ClOrdID
        order_id = msg.getField(id_tag)
        order_object[id_tag] = order_id                   #store the id inside as well

        self.ORDERS_DICT[order_id] = order_object         #add to list of order info using the ID as key
        self.LASTEST_ORDER         = order_object         #remember the latest order for easier accessing
        printv("\n=====> Order recorded in memory with id = {}\n".format(order_id))
    
    def _retrieve_json_order(self, id):
        if id == -1 or id == '-1' or id == 'latest':
            return self.LASTEST_ORDER
        return self.ORDERS_DICT[id]

    
    '''=========================================================================
    Message Templates
    '''
    
    
    def __get_val(self,input_dict, tag, replace_with):
        '''Get values from user input and replace them if they are not present'''
        try:
            val = input_dict[tag]
        except KeyError:
            val = replace_with
        return val

    # def standard_new_order(self,kargs):
    #     msg = self._make_standard_header(fix.MsgType_NewOrderSingle)
    #     msg.setField(fix.ClOrdID(self.genOrderID()))                 #11=Unique order
    #     msg.setField(fix.StringField(60,(dt.datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f"))[:-3]))    #60 = transaction time
    #     msg.setField(fix.TimeInForce(_timeInForce))   #-----> system complained of missing tag. This order is good for the day or for the session

    def _NewOrderSingle(self,kargs):
        '''
        _, options = parse_fix_options("1 -59 -55 EUR/USD -44 1.145 -38 100000")
        wanted_tags=[40,54,38,55,167]

        _price       = kargs['44']          #Price
        _timeInForce = kargs['59']          #TimeInForce
        _orderQty    = kargs['38']          #OrderQty
        _asset       = kargs['55']          #Symbol
        _side        = kargs['54']          #Side
        _ordType     = kargs['40']          #OrdType
        _secType     = kargs['167']         #SecurityType
        '''

        _asset       = kargs['55']                  #Symbol
        _timeInForce = self.__get_val(kargs,'59',fix.TimeInForce_FILL_OR_KILL)          #TimeInForce
        _orderQty    = float(kargs['38'])          #OrderQty
        _side        = kargs['54']          #Side tag 54
        _ordType     = kargs['40']          #OrdType
        _secType     = self.__get_val(kargs,'167','CS')         #SecurityType

        msg = self._make_standard_header(fix.MsgType_NewOrderSingle)
        msg.getHeader().setField(fix.BeginString(fix.BeginString_FIX42))
        msg.getHeader().setField(fix.MsgType(fix.MsgType_NewOrderSingle)) #35=D
        msg.setField(fix.ClOrdID(self.genOrderID()))                 #11=Unique order

        msg.setField(fix.TimeInForce(_timeInForce))   #-----> system complained of missing tag. This order is good for the day or for the session
        #print("--After ClOrdID")
        msg.setField(fix.SecurityType(_secType))         #-----> added because system complained about missing tag. instead of 'FOR' it could be fix.SecurityType_FOR. 'FOR' is for forex
        msg.setField(fix.HandlInst(fix.HandlInst_AUTOMATED_EXECUTION_ORDER_PRIVATE_NO_BROKER_INTERVENTION)) #21=3 (Manual order, best execution)
        msg.setField(fix.Symbol(_asset)) #55=SMBL ? the assest we wish to trade (e.g. 'EUR/USD', 'AAPL', 'SBUX', etc)
        msg.setField(fix.Side(_side))    #54=1 Buy
        msg.setField(fix.OrdType(_ordType)) #40=2 Limit order
        #print("--After OrdType")
        msg.setField(fix.OrderQty(_orderQty)) #38=100
        if _ordType == '2':
            _price       = float(kargs['44'])          #Price
            msg.setField(fix.Price(_price))          #tag 44 price
        #print("--After Price")
        time_stamp = int(dt.datetime.timestamp(dt.datetime.utcnow()))
        msg.getHeader().setField(fix.SendingTime(1))
        msg.setField(fix.StringField(60,(dt.datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f"))[:-3]))
        return msg

    def _OrderCancelRequest(self, kargs, wanted_tags=[11]):

        #----Extract keys
        _previous_id = self.__get_val(kargs,'41',-1)    #get id from previous order to cancel. If not provided default to the last one

        #----Retrieve order stored in memory or database
        order_object = self._retrieve_json_order(_previous_id)

        #----Create standard header
        msg = self._make_standard_header(fix.MsgType_OrderCancelRequest)
        # msg.getHeader().setField(fix.MsgType(fix.MsgType_OrderCancelRequest))     #35 = F
        # import pdb;pdb.set_trace()
        msg.setField(fix.ClOrdID(self.genOrderID()))                              #11=Unique order id

        #----Load data from previous order using the stringField method of Quickfix instead of calling by specific tag names
        for tag in wanted_tags:
            value = order_object[tag]
            if tag == 11 or tag == '11':                              #we change 11 to 41 because 11 will be used for this order's id, while 41 is the id of the order we want to cancel
                tag = fix.OrigClOrdID().getField()                    #Get the tag number (it should be 41 but this is more resistant to changes in protocol)
            msg.setField(fix.StringField(tag,value))

        #----Add transaction time
        msg.setField(fix.StringField(60,(dt.datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f"))[:-3]))    #60 = transaction time

        return msg

    
    def _OrderStatusRequest(self,kargs):

        _side = self.__get_val(kargs,'54',fix.Side_BUY)#----Extract keys
        _previous_id = self.__get_val(kargs,'41',-1)    #get id from previous order to cancel. If not provided default to the last one

        msg = self._make_standard_header()
        msg.getHeader().setField(fix.MsgType(fix.MsgType_OrderStatusRequest))       #35 = H
        msg.setField(fix.ClOrdID(_previous_id))                                              # 11 = order id
        msg.setField(fix.Side(_side))

        return msg

  
    
    '''=========================================================================
    User interface
    '''
    
    # def buy_limit(self,symbol,):
    #     msg = self.standard_new_order()
    #     msg.setField(54,"1") #Side <54> field , 1= BUY, 2=SELL
    #     msg.setField(40,"2")  #1 = Market, 2 = Limit
        
        
    #     self._record_json_order(msg,wanted_tags=[40,54,38,55,167])
    #     fix.Session.sendToTarget(msg, self.sender,self.target)

    # def buy_market(self,**kargs):
    #     msg = self.standard_new_order()
    #     msg.setField(54,"1") #Side <54> field 



        
        # kargs['54'] = fix.Side_BUY
        # kargs['40'] = 1
        # msg = self._NewOrderSingle(kargs)
        # #msg.setField(fix.Account(self.settingsDic.getString('Account')))
        # self._record_json_order(msg,wanted_tags=[40,54,38,55,167])
        # fix.Session.sendToTarget(msg, self.sender,self.target)
    # def sell_limit(self,**kargs):
    #     msg = self.standard_new_order()
    #     msg.setField(54,"2") #Side <54> field 
    # def sell_market(self,**kargs):
    #     msg = self.standard_new_order()
    #     msg.setField(54,"2") #Side <54> field 
    
    
    def OneOrder(self,**kargs):
        msg = self._NewOrderSingle(kargs)
        self._record_json_order(msg,wanted_tags=[40,54,38,55,167])
        fix.Session.sendToTarget(msg, self.sender,self.target)

    # def sell(self,**kargs):
    #     kargs['54'] = fix.Side_SELL
    #     msg = self._NewOrderSingle(kargs)
    #     self._record_json_order(msg,wanted_tags=[40,54,38,55,167])
    #     fix.Session.sendToTarget(msg, self.sender,self.target)
    # def buy(self,**kargs):
    #     kargs['54'] = fix.Side_BUY
    #     msg = self._NewOrderSingle(kargs)
    #     # msg.setField('6','1.145')
    #     self._record_json_order(msg,wanted_tags=[40,54,38,55,167])
    #     fix.Session.sendToTarget(msg, self.sender,self.target)
    
    # def limit_buy(self, **kargs):
    #     kargs['40'] = fix.OrdType_LIMIT
    #     kargs['54'] = fix.Side_BUY
    #     msg = self._NewOrderSingle(kargs)

    #     self._record_json_order(msg,wanted_tags=[40,54,38,55,167])
    #     fix.Sessions.sendToTarget(msg,self.sender,self.target)
    #     #fix.Session.sendToTarget(msg, self.sender,self.target)

    
    # def limit_sell(self, **kargs):
    #     kargs['40'] = fix.OrdType_LIMIT
    #     kargs['54'] = fix.Side_SELL
    #     msg = self._NewOrderSingle(kargs)

    #     self._record_json_order(msg,wanted_tags=[40,54,38,55,167])
    #     fix.Sessions.sendToTarget(msg,self.sender,self.target)
    #     #fix.Session.sendToTarget(msg, self.sender,self.target)
    

    
    def cancel_order(self,**kargs): 
        msg = self._OrderCancelRequest(kargs,wanted_tags=[11,54,38,55,167])
        fix.Session.sendToTarget(msg, self.sender,self.target)

    
    def check_order_status(self,**kargs):
        msg = self._OrderStatusRequest(kargs)
        fix.Session.sendToTarget(msg,self.sender,self.target)
        #fix.Session.sendToTarget(msg, self.sender,self.target)


    
    def logout(self):
        msg = fix.Message()
        msg.getHeader().setField(fix.BeginString(fix.BeginString_FIX42))
        msg.getHeader().setField(fix.MsgType(fix.MsgType_Logout))

        fix.Session.sendToTarget(msg, self.sender,self.target)
        #fix.Session.sendToTarget(msg, self.sender,self.target)
    def resetSeqLogOn(self):
        #send a message to server
        msg = self._make_standard_header(fix.MsgType_Logon)
        # msg.getHeader().setField(fix.BeginString(fix.BeginString_FIX42))
        # msg.getHeader().setField(fix.MsgType(fix.MsgType_Logosn))
        msg.getHeader().setField(fix.ResetSeqNumFlag(True))
        msg.setField(98,"0") #Encryp_method
        msg.setField(108,"30") #HeartBtInt
        # print("msg msg msg",msg)c
        fix.Session.sendToTarget(msg, self.sender,self.target)
        # fix_str = unicode_fix(msg.toString())
        # print("fix_str",    fix_str)

if __name__ == '__main__':
    pass