__all__ = ['OrderManager','FixDecoder','PairContainer','OrderedMessage',
           'TagPair','print_fix_string','unicode_fix','isSymbolTag']

from bs4 import BeautifulSoup as Soup     #to parse XML and other files
import sys
import quickfix as fix
import pandas as pd
import datetime as dt
from datetime import datetime 
from . import print0,printv,printvv,printvvv 
import os
import time

class OrderManager(object):
    '''
    Manage and keep track of buy and sell orders in the session
    '''
    def __init__(self):
        self.open_order_ids = []        #sort of stack structure to store ids in order, but also it be accessed out of order
        self.history        = []        #chronological record of trades

    def get_last_open_order(self):
        return self.open_order_ids[-1]

    def remove_last_open_order(self):
        self.open_order_ids.pop()

    def pop_last_open_order(self):
        order_id = self.open_order_ids.pop()
        return order_id

    def add_order(self,id):
        self.open_order_ids.append(id)
        self.history.append(id)

    def remove_order(self,id):
        self.open_order_ids.remove(id)


    def close_order(self,id):
        pass

    #Checkers
    def isUnique(self,id):
        if id in self.history:
            return False
        return True

#===============================================================================
def get_any_tag(message, tag):
    '''general purpose tag value extractor'''
    try:
        val = message.getField(tag)
    except:
        try:
            val = message.getHeader.getField(tag)
        except:
            printv("Failed to read tag '{}' from message. Tag may be missing".format(tag))
            raise ValueError
    return val

class FixDecoder(object):
    """
    A Collection of tools to decode a FIX message.
    """
    def __init__(self, datadictionary='FIX42.xml'):
        self.path_dict = datadictionary
        self.__build_dictionary()   #create the dictionary to store names read from the data dictionary
        self.orderbook = None

        #------data converters
        init_time = dt.datetime.utcnow()

        #Some definition dictionaries for clearer decoding. If it becomes too long, this class could be moved to a different file to avoid cluttering the client class
        self._ExecInst     =  {'tag':'18',
                              'G':'All or none',
                              'u':'Partial fill'}

        self._ExecType    =  {'tag':'150',
                              '0':'New',
                              '4':'Canceled',
                              '5':'Replaced',
                              '6':'Pending Cancel',
                              '8':'Rejected',
                              '9':'Suspended',
                              'E':'Pending Replace',
                              'F':'Trade (partial or fill)'}

        self._OrderStatus =  {'tag':'39',
                              '0':'New',
                              '1':'Partially Filled',
                              '2':'Filled',
                              '4':'Canceled',
                              '6':'Pending Canceled',
                              '8':'Rejected',
                              'E':'Pending Replace'}

        self._MDEntryType =  {'tag':'269',
                              '0':'Bid',
                              '1':'Offer',
                              '2':'Trade',
                              '3':'Index Value',
                              '4':'Opening Price',
                              '5':'Closing Price',
                              '6':'Settlement Price',
                              '7':'Trading Session High Price',
                              '8':'Trading Session Low Price',
                              '9':'Trading Session VWAP Price',
                              'A':'Imbalance',
                              'B':'Trade Volumne',
                              'C':'Open Interest'}
        self._CxlRejReason = {'tag':'102',
                              '0' : 'Too late to cancel',
                              '1' : 'Unknown order',
                              '2' : 'Broker / Exchange Option',
                              '3' : 'Order already in Pending Cancel or Pending Replace status',
                              '4' : 'Unable to process Order Mass Cancel Request <q>',
                              '5' : 'OrigOrdModTime <586> (586) did not match last TransactTime <60> (60) of order',
                              '6' : 'Duplicate ClOrdID <11> () received',
                              '99': 'Other',
                              -1: 'Unknown reason'}

        self._CxlRejResponseTo = {'tag':'434',
                                  '1'  : 'Order Cancel Request <F>',
                                  '2' : 'Order Cancel/Replace Request <G>'}

    def __build_dictionary(self):
        '''This function was based on the one here: http://quickfix.13857.n7.nabble.com/MessageCracker-python-td6756.html'''
        self.datadict  = {}
        handler = open(self.path_dict).read()
        soup = Soup(handler,'xml')
        for s in soup.findAll('fields'):
            for m in s.findAll('field'):
                msg_attrs =m.attrs
                self.datadict[int(msg_attrs["number"])]=msg_attrs["name"]

    ''' ************************************************************************
    Operator Overloading
    '''
    def __getitem__(self,key):
        k = key
        if type(key) == str:
            k = int(key)

        return self.datadict[k]

    def __setitem__(self,key,value):
        k = key
        if type(key) == str:
            k = int(key)

        self.datadict[k] = value


    def keys(self):
        return self.datadict.keys()

    def items(self):
        return self.datadict.items()

    def values(self):
        return self.datadict.values()

    '''*************************************************************************
    Getters and Tools
    '''
    @staticmethod
    def get_MsgType(message):
        return message.getHeader().getField(35)

    def _get_MsgType(self, message):
        '''Return a string with the value of tag 35'''
        return message.getHeader().getField(35)     #35 is the tag for message type

    def _get_SendingTime(self,message):
        return message.getHeader().getField(52)

    def _get_error_report(self,message):
        '''return error data from a message containing the tag 35=3'''
        error_text    = message.getField(58)  #tag 58 usually contains an error messages
        reference_tag = message.getField(371) #tag 371 tells the tag number which is causing trouble
        ref_msg_type  = message.getField(372)
        return (error_text,reference_tag,ref_msg_type)

    def _get_text(self,message):
        try:
            return message.getField(58)     #tag 58 contains text, usually an error message
        except:
            return "No text tag (58) included"

    @staticmethod
    def get_any_tag(message, tag):
        '''general purpose tag value extractor'''
        try:
            val = message.getField(tag)
        except:
            try:
                val = message.getHeader().getField(tag)
            except:
                # print("Failed to read tag '{}' from message".format(tag))
                return -1
        return val

    @staticmethod
    def get_FIX_dict(msg):
        '''returns a dictionary of the tags and values from a Quickfix message. '''
        msg_str = msg.toString()
        msg_dict = {}
        tag_value_pairs = msg_str.split('\x01')[:-1]
        #pairs = [p.split('=') for p in tag_value_pairs]
        #pairs = [(int(p[0]),p[1]) for p in pairs]
        for pair in tag_value_pairs:
            tag,val = pair.split('=')
            tag = int(tag)
            msg_dict.setdefault(tag, []).append(val)

        return msg_dict

    def format_wrapper(self, *args):
        #fmt_str = args[0].format(*args[1:])
        input_str = args[0]
        split_by_colon = input_str.split(':')  #separate the two sides of the string

        fmt_str = "{:<35} : {}".format(split_by_colon[0],split_by_colon[1])
        fmt_str = fmt_str.format(*args[1:])

        #fmt_str = "{:<35}:{}".format(*args)
        return fmt_str

    def extract_execution_report(message):
        execType            = self.get_any_tag(message,150)       #
        ord_status          = self.get_any_tag(message,39)        #tells if the order was executed
        quant_fillied       = self.get_any_tag(message,14)        #qunatity filled from the order
        quant_not_filled    = self.get_any_tag(message,151)
        exchange_rate       = self.get_any_tag(message,9329)
        commission          = self.get_any_tag(message,12)        #comission charged by broker on this trade
        orderID             = self.get_any_tag(message,37)
        return {'orderID':orderID,'execType':execType,'ord_status':ord_status,'quant_fillied':quant_fillied,
                'quant_not_filled':quant_not_filled,'exchange_rate':exchange_rate,'commission':commission}

    def extract_msg_data(self,msg_type,message):
        if msg_type == '8':
            self.extract_execution_report(message)

        
    def print_report(self,message):
        # time.sleep(5)
        print = printvv

        #=======================================================================
        
        msg_type = self._get_MsgType(message)
        print('='*80)
        if msg_type == '0':
            print("HeartBeat (35='0')")
            return msg_type,0
            # pass   #a zero means a heartbeat

        elif msg_type == '3': 
             #
            error,ref_tag,ref_MsgType = self._get_error_report(message)
            #ref_MsgType = self.get_any_tag(372)     #the message type being referenced by the error
            print("Message rejected (35='3')")
            print(self.format_wrapper("Reference Tag (tag 371): {}",ref_tag))
            print(self.format_wrapper("Reference Message type (tag 372): {}",ref_MsgType))
            print(self.format_wrapper("Reason (tag 58):\n {}",self._get_text(message)))
            print("Reference Tag (tag 371): {}".format(ref_tag))
            print("Reference Message type (tag 372): {}".format(ref_MsgType))
            print("reason (tag 58): {}".format(error))
            return msg_type,0

        elif msg_type == '5':           #this is a logout message
            print("Logout Message (35={})".format(msg_type)) 
            return msg_type,0

        elif msg_type == '8': #Execution report

            OrderID=self.get_any_tag(message,37) #Unique identifier for Order as assigned by broker
            ExecID=self.get_any_tag(message,17)
            OrdStatus=self.get_any_tag(message,39) 
            # 0 = New; 1 = Partially filled;2 = Filled;3 = Done for day;4 = Canceled; 6 = Pending Cancel (e.g. result of Order Cancel Request <F>);7 = Stopped
            ExecType=self.get_any_tag(message,150) 
            ClOrdID=self.get_any_tag(message,11) 
            # Describes the specific ExecutionRpt <8> (i.e. Pending Cancel) while OrdStatus <39> will always identify the current order status (i.e. Partially Filled);
            # 0 = New; 1 = Partially filled;2 = Filled;3 = Done for day;4 = Canceled; 6 = Pending Cancel (e.g. result of Order Cancel Request <F>);7 = Stopped
            CumQty=self.get_any_tag(message,14) #Total number of shares filled.

            Symbol=self.get_any_tag(message,55)
            Side=self.get_any_tag(message,54) #1=Buy 2=Sell
            LastShares=self.get_any_tag(message,32) #Quantity of shares bought/sold on this (last) fill
            LastPx=self.get_any_tag(message,31) # Price of this (last) fill

            
            # print("Execution Report (35='{}')".format(msg_type))
            # print(self.format_wrapper("Execution Type (tag 150): '{}' => {}", ExecType,self._ExecType[ExecType]))
            print(self.format_wrapper("Order Status (tag 39): '{}' => {}",OrdStatus,self._OrderStatus[OrdStatus]))
            # print(self.format_wrapper("Quantity filled (tag 14): {}",quant_fillied))
            # print(self.format_wrapper("Quantity NOT filled (tag 151): {}",not_filled))
            # print(self.format_wrapper("USD Exchange rate (tag 9329): {}", exchange_rate))
            # print(self.format_wrapper("Commission paid (tag 12): {}",commission))
            print(self.format_wrapper("Text (tag 58):\n {}",self._get_text(message)))
            return msg_type, {'ExecType':ExecType,'OrderID':OrderID,'ClOrdID':ClOrdID,'Side':Side,'Symbol':Symbol,'LastPx':float(LastPx),'LastShares':float(LastShares)}

        elif msg_type == '9':

            # OrderID= self.get_any_tag(message,37) #Unique identifier for Order as assigned by broker.
            # OrdStatus = self.get_any_tag(message,39) #Identifies current status of order.
            # 0 = New; 1 = Partially filled;2 = Filled;3 = Done for day;4 = Canceled; 6 = Pending Cancel (e.g. result of Order Cancel Request <F>);7 = Stopped ;8 = Rejected
            
            
            original_id       = self.get_any_tag(message,41) #ClOrdID <11> of the previous order
            order_status      = self.get_any_tag(message,39)
            reject_reason     = self.get_any_tag(message,102)
            # reject_responseTo = self.get_any_tag(message,434)
            id_by_broker      = self.get_any_tag(message,37)        #order id assigned by the broker
            # ClOrdID           = self.get_any_tag(message,11)        #order id for client order getting rejected

            print("Order Cancel Reject (35={})".format(msg_type))
            print(self.format_wrapper("ID of order to be canceled: {}",original_id))
            print(self.format_wrapper("ID given by broker (tag 37): {}",id_by_broker))
            # print(self.format_wrapper("ID of client order (ClOrdID tag 11): {}",ClOrdID))
            print(self.format_wrapper("Order Status (tag 39): '{}' => {}'",order_status,self._OrderStatus[order_status]))
            print(self.format_wrapper("Reject reason (tag 102): '{}' => {}",reject_reason,self._CxlRejReason[reject_reason]))
            # print(self.format_wrapper("Reject ResponseTo (tag 434): '{}' => {}",reject_responseTo,self._CxlRejResponseTo[reject_responseTo]))
            # print()
            return msg_type,0 

        elif msg_type == 'A':
            print("Logon Message (35='A')")
            return msg_type,0   
        else:
            print("Message Type 35='{}' NOT IMPLEMENTED".format(msg_type))
            return msg_type,0 

#===============================================================================

class PairContainer(dict):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __getitem__(self, key):
        val = dict.__getitem__(self, key)
        #print 'GET', key
        return val

    def __setitem__(self, key, val):
        #print 'SET', key, val
        dict.__setitem__(self, key, val)

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return '%s(%s)' % (type(self).__name__, dictrepr)

    def update(self, *args, **kwargs):
        #print 'update', args, kwargs
        for k, v in dict(*args, **kwargs).iteritems():
            self[k] = v


class OrderedMessage(object):
    def __init__(self,pair_objs, order=[8,9,35,49,56,34,52]):
        self.pairs     = pair_objs
        self.new_order = []
        self.order     = [str(tag) for tag in order]
        self.tags      = [pair.get_tag() for pair in pair_objs]   #this will preserve the original order
        self.dict      = {}                 #maps tags to the pair objects (this sounds so wrong on a performance level, but for now it is just a hack to test)

        print()
        for pair in pair_objs:
            self.dict.update(pair.get_dict())

    def arrange_pairs(self):

        #if no order is provided simply set self.new_order as self.pairs
        if len(self.order) == 0:
            self.new_order = self.pairs    #be careful. This is actually a reference to self.pairs, not a copy
            return


        num_fields = len(self.pairs)
        self.new_order = [None]*num_fields

        #First add all required header tags
        count_idx = 0
        for tag in self.order:
            try:
                #print("Tag inside TRY:",tag)
                pair = self.dict[tag]
                #print("PRINT IS:",pair)
                #self.new_order.append(pair)
                self.new_order[count_idx] = pair
                count_idx += 1
            except KeyError as err:
                print(err)
                print("'{}' is a required field in any message to Fortex FIX server".format(tag))
                exit(1)

        for tag in self.tags:
            if tag in self.order:
                continue            #we have already covered the required tags, so we can ignore them

            if tag == '10':
                pair = self.dict[tag]
                self.new_order[num_fields-1] = pair                #tag 10 is the checksum and always goes to the end
            else:
                self.new_order[count_idx] = self.dict[tag]
                count_idx += 1


    def toString(self):
        #arrange before converting
        self.arrange_pairs()
        print(self.new_order)
        str_msg = "\x01".join([pair.toString() for pair in self.new_order]) + '\x01'
        return str_msg

class TagPair(object):
    def __init__(self,tag_val_str):
        split_field = tag_val_str.split('=')
        split_field = [item.strip() for item in split_field]

        self.tag = split_field[0]
        self.val = split_field[1]
        #self.tag,self.val = [(tag.strip(),val.strip()) for tag,val in tag_val_str.split('=')]
        #self.tag,self.val = [[item.strip() for item in pair] for pair in  ]
        #self.tag = str(tag)
        #self.val = str(val)

    def toString(self):
        return str(self.tag) + '=' + str(self.val)
    def get_tag(self):
        return self.tag
    def get_val(self):
        return self.val
    def get_dict(self):
        return {self.tag:self}
    '''
    Overloading
    '''
    def __str__(self):
        return "{}={}".format(self.get_tag(),self.get_val())
    __repr__ = __str__

    def __lt__(self,other):
        if self.tag < other.tag:
            return True
        else:
            return False
    def __gt__(self,other):
        if self.tag > other.tag:
            return True
        else:
            return False

def print_fix_string(string):
    """Take string and replace characters FIX '|' characters to ones that appear correctly in the terminal and print it"""
    bar_in_unicode = '\x01'  # '|' from FIX messages in unicode
    new_str = string.replace(bar_in_unicode, '|')
    print(new_str)

def unicode_fix(string):
    """Take string and replace characters FIX '|' characters to ones that appear correctly in the terminal and return it"""
    bar_in_unicode = '\x01'  # '|' from FIX messages in unicode
    new_str = string.replace(bar_in_unicode, '|')
    return new_str

def isSymbolTag(tag):
    if tag == '55' or tag==55 or tag=='-55' or tag==-55:
        return True
    return False
 
if __name__ == '__main__':
    pass     
