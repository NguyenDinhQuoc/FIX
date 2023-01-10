__all__ = ['BaseFixClient']
#import time
import datetime as dt
import quickfix as fix 
import quickfix42 as fix42 
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
    transaction_list   = []
    LASTEST_ORDER = {}
    LASTEST_ORDER_ID=0
    
    
    #Keep track of orders and ids
    open_subs   = []
    open_orders = []

    '''=========================================================================
    Internal message methods
    '''
    def get_any_tag(self,message, tag):
        '''general purpose tag value extractor'''
        try:
            val = message.getField(tag)
        except:
            try:
                val = message.getHeader().getField(tag)
            except:
                print("Failed to read tag '{}' from message".format(tag))
                return -1
        return val

    def onCreate(self, sessionID):
        return


    def onLogon(self, sessionID):
        self.sessionID = sessionID
        # print('on Logon')
        # self.resetSeqLogOn()
        return


    def onLogout(self, sessionID):
        # print("\n onLogout")
        #fix.Session.lookupSession(sessionID).logout();
        return


    def toAdmin(self, message,sessionID):
        fix_str = unicode_fix(message.toString())
        # print("\n toAdmin: \n{}".format(fix_str))
        return


    def fromAdmin(self, message, sessionID):
        fix_str = unicode_fix(message.toString())
        # print("\n fromAdmin: Incoming Msg (fromAdmin):\n{}".format(fix_str))
        # printvv("\nIncoming Msg (fromAdmin):\n{}".format(fix_str))
        msg_type,report=self.decoder.print_report(message) 
        if msg_type=='8':
            ExecType=report["ExecType"]
            if ExecType == '0':
                OrderID=report['OrderID']
                ClOrdID=report['ClOrdID']
                # print('adding orderID to json file',OrderID)
                self.add_OrderID_37_into_json_oder(ClOrdID,OrderID)
            if ExecType in ['1','2']:
                self.transaction_list.append(report)
        return


    def toApp(self, message, sessionID):
        fix_str = unicode_fix(message.toString())
        # print("\n toApp: \n{}".format(fix_str))
        return

    def fromApp(self, message, sessionID):
        '''Capture Messages coming from the counterparty'''
        
        # er=fix42.ExecutionReport(message)
        # print("er",unicode_fix(er.toString()))
        
        fix_str = unicode_fix(message.toString())
        # print("\n fromApp ",fix_str) 
        msg_type,report=self.decoder.print_report(message) 
        if msg_type=='8':
            ExecType=report["ExecType"]
            if ExecType == '0':
                OrderID=report['OrderID']
                ClOrdID=report['ClOrdID']
                # print('adding orderID to json file',OrderID)
                self.add_OrderID_37_into_json_oder(ClOrdID,OrderID)
            if ExecType in ['1','2']:
                self.transaction_list.append(report)
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

        ClOrdID = msg.getField(11)
        order_object[11] = ClOrdID                   #store the id inside as well

        self.ORDERS_DICT[ClOrdID] = order_object         #add to list of order info using the ID as key
        self.LASTEST_ORDER         = order_object         #remember the latest order for easier accessing
        
        printv("\n=====> Order recorded in memory with id = {}\n".format(ClOrdID))
    def add_OrderID_37_into_json_oder(self,ClOrdID,OrderID):
        self.LASTEST_ORDER_ID=OrderID
        self.ORDERS_DICT[ClOrdID]["OrderID"]=OrderID

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
            if tag == 11 or tag == '11':                             
                tag = fix.OrigClOrdID().getField()                    #tag 41 of cancel request message is the tag 11 of order message
            msg.setField(fix.StringField(tag,value))
        # print(order_object)
        if 'OrderID' in order_object.keys(): # some case, order_object wasn't recorded by time of cancel request
            msg.setField(fix.StringField(37,order_object['OrderID']))
        # msg.setField(fix.StringField(37,self.LASTEST_ORDER_ID))

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
    

    
    def cancel_order(self,**kargs): 
        msg = self._OrderCancelRequest(kargs,wanted_tags=[11,54,38,55,167])
        fix.Session.sendToTarget(msg, self.sender,self.target)

    
    def check_order_status(self,**kargs):
        msg = self._OrderStatusRequest(kargs)
        fix.Session.sendToTarget(msg,self.sender,self.target)
        #


    
    def logout(self):
        msg = fix.Message()
        msg.getHeader().setField(fix.BeginString(fix.BeginString_FIX42))
        msg.getHeader().setField(fix.MsgType(fix.MsgType_Logout))

        fix.Session.sendToTarget(msg, self.sender,self.target)
    def resetSeqLogOn(self):
        #send a message to server
        msg = self._make_standard_header(fix.MsgType_Logon)
        msg.getHeader().setField(fix.ResetSeqNumFlag(True))
        msg.setField(98,"0") #Encryp_method
        msg.setField(108,"30") #HeartBtInt
        fix.Session.sendToTarget(msg, self.sender,self.target)
        # fix_str = unicode_fix(msg.toString())
        # print("fix_str",    fix_str)

if __name__ == '__main__':
    pass