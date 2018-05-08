from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract as IBcontract
from threading import Thread
import queue
import datetime

DEFAULT_HISTORIC_DATA_ID=50
DEFAULT_GET_CONTRACT_ID=43

## market for when queue is finished
FINISHED = object()
STARTED = object()
TIME_OUT = object()

class completedHistQueue(object):

    def __init__(self, queue_to_finish):
        self._queue = queue_to_finish
        self.status = STARTED

    def get(self, timeout):
        """
        Returns a list of queue elements once timeout is finished, or a FINISHED flag is received in the queue
        :param timeout: how long to wait before giving up
        :return: list of queue elements
        """
        contents_of_queue=[]
        finished=False
        while not finished:
            try:
                current_element = self._queue.get(timeout=timeout)
                if current_element is FINISHED:
                    finished = True
                    self.status = FINISHED
                else:
                    contents_of_queue.append(current_element)
                    ## keep going and try and get more data
            except queue.Empty:
                ## If we hit a time out it's most probable we're not getting a finished element any time soon
                ## give up and return what we have
                finished = True
                self.status = TIME_OUT
        return contents_of_queue

    def timed_out(self):
        return self.status is TIME_OUT

class TestWrapper(EWrapper):
    """
    The wrapper deals with the action coming back from the IB gateway or TWS instance
    We override methods in EWrapper that will get called when this action happens, like currentTime
    """
    def __init__(self):
        self._my_contract_details = {}
        self._my_historic_data_dict = {}

    ## error handling code
    def init_error(self):
        error_queue=queue.Queue()
        self._my_errors = error_queue
    
    ## get error thrown
    def get_error(self, timeout=5):
        if self.is_error():
            try:
                return self._my_errors.get(timeout=timeout)
            except queue.Empty:
                return None
        return None

    ## boolean, check if is error
    def is_error(self):
        an_error_if=not self._my_errors.empty()
        return an_error_if

    ## get the error, put into error queue
    def error(self, id, errorCode, errorString):
        ## Overriden method
        errormsg = "IB error id %d errorcode %d string %s" % (id, errorCode, errorString)
        self._my_errors.put(errormsg)

    ## get contract details code
    def init_contractdetails(self, reqId):
        contract_details_queue = self._my_contract_details[reqId] = queue.Queue()
        return contract_details_queue

    ## retrieved contract details, put into contract details dict
    def contractDetails(self, reqId, contractDetails):
        ## overridden method
        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)
        self._my_contract_details[reqId].put(contractDetails)

    ## mark finished receiving contract details.
    def contractDetailsEnd(self, reqId):
        ## overriden method
        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)
        self._my_contract_details[reqId].put(FINISHED)

    ## init historical data dictionary to empty queues
    def init_historicprices(self, tickerid):
        historic_data_queue = self._my_historic_data_dict[tickerid] = queue.Queue()
        return historic_data_queue

    ##
    def historicalData(self, tickerid , bar):
        ## Overriden method
        ## Note I'm choosing to ignore barCount, WAP and hasGaps but you could use them if you like
        bardata=(bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)
        historic_data_dict=self._my_historic_data_dict
        ## Add on to the current data
        if tickerid not in historic_data_dict.keys():
            self.init_historicprices(tickerid)
        historic_data_dict[tickerid].put(bardata)

    def historicalDataEnd(self, tickerid, start:str, end:str):
        ## overriden method
        if tickerid not in self._my_historic_data_dict.keys():
            self.init_historicprices(tickerid)
        self._my_historic_data_dict[tickerid].put(FINISHED)

    ## Time telling code
    def init_time(self):
        time_queue=queue.Queue()
        self._time_queue = time_queue
        return time_queue

    ## Scanner Parmams telling code
    def init_scanner_params_xml(self):
        scanner_params_xml_queue=queue.Queue()
        self._scanner_params_xml_queue = scanner_params_xml_queue
        return scanner_params_xml_queue

    def currentTime(self, time_from_server):
        ## Overriden method
        self._time_queue.put(time_from_server)

    def scannerParameters(self, xml_from_server):
        ## Overridden method
        self._scanner_params_xml_queue.put(xml_from_server)

class TestClient(EClient):

    """
    The client method
    We don't override native methods, but instead call them from our own wrappers
    """

    def __init__(self, wrapper):
        ## Set up with a wrapper inside
        EClient.__init__(self, wrapper)

    def resolve_ibContract(self, ibContract, reqId=DEFAULT_GET_CONTRACT_ID):
        """
        From a partially formed contract, returns a fully fledged version
        :returns fully resolved IB contract
        """
        ## Make a place to store the data we're going to return
        contract_details_queue = completedHistQueue(self.init_contractdetails(reqId))
        print("Getting full contract details from the server... ")
        self.reqContractDetails(reqId, ibContract)
        ## Run until we get a valid contract(s) or get bored waiting
        MAX_WAIT_SECONDS = 10
        new_contract_details = contract_details_queue.get(timeout = MAX_WAIT_SECONDS)
        while self.wrapper.is_error():
            print(self.get_error())
        if contract_details_queue.timed_out():
            print("Exceeded maximum wait for wrapper to confirm finished - seems to be normal behaviour")
        if len(new_contract_details)==0:
            print("Failed to get additional contract details: returning unresolved contract")
            return ibContract
        if len(new_contract_details)>1:
            print("got multiple contracts using first one")
        new_contract_details=new_contract_details[0]
        resolved_ibContract=new_contract_details.summary
        return resolved_ibContract

    def getHist(self, ibContract, duration="1 Y", barSize="1 day", whatToShow = "TRADES", tickerid=DEFAULT_HISTORIC_DATA_ID):
        """
        Returns historical prices for a contract, up to today
        ibcontract is a Contract
        :returns list of prices in 4 tuples: Open high low close volume
        """
        ## Make a place to store the data we're going to return
        historic_data_queue = completedHistQueue(self.init_historicprices(tickerid))
        # Request some historical data. Native method in EClient
        self.reqHistoricalData(
            tickerid,  # tickerId,
            ibContract,  # contract,
            datetime.datetime.today().strftime("%Y%m%d %H:%M:%S %Z"),  # endDateTime,
            duration,  # durationStr,
            barSize,  # barSizeSetting,
            whatToShow,  # whatToShow,
            1,  # useRTH,
            1,  # formatDate
            False,  # KeepUpToDate <<==== added for api 9.73.2
            [] ## chartoptions not used
        )
        ## Wait until we get a completed data, an error, or get bored waiting
        MAX_WAIT_SECONDS = 10
        print("Getting historical data from the server... could take %d seconds to complete " % MAX_WAIT_SECONDS)
        historic_data = historic_data_queue.get(timeout = MAX_WAIT_SECONDS)
        while self.wrapper.is_error():
            print(self.get_error())
        if historic_data_queue.timed_out():
            print("Exceeded maximum wait for wrapper to confirm finished - seems to be normal behaviour")
        self.cancelHistoricalData(tickerid)
        return historic_data

    def speaking_clock(self):
        """
        Basic example to tell the time
        :return: unix time, as an int
        """
        print("Getting the time from the server... ")
        ## Make a place to store the time we're going to return
        ## This is a queue
        time_storage=self.wrapper.init_time()
        ## This is the native method in EClient, asks the server to send us the time please
        self.reqCurrentTime()
        ## Try and get a valid time
        MAX_WAIT_SECONDS = 10
        try:
            current_time = time_storage.get(timeout=MAX_WAIT_SECONDS)
        except queue.Empty:
            print("Exceeded maximum wait for wrapper to respond")
            current_time = None
        while self.wrapper.is_error():
            print(self.get_error())
        return current_time

    def get_scanner_params_as_xml(self):
        """
        We want to see what are the valid parameters for a scanner
        """
        print ("Getting possible options for scanner subsscription...")
        scanner_params_storage = self.wrapper.init_scanner_params_xml()
        ## This is the native method in EClient, aks the server to send us the scanner
        ## params xml please.
        self.reqScannerParameters()
        ## Try and get a valid scanner parameters xml
        MAX_WAIT_SECONDS = 10
        try:
            scanner_params_xml = scanner_params_storage.get(timeout=MAX_WAIT_SECONDS)
        except queue.Empty:
            print("Exceeded maximum wait for wrapper to respond: scanner params xml")
            scanner_params_xml = None
        while self.wrapper.is_error():
            print(self.get_error())
        return scanner_params_xml

class TestApp(TestWrapper, TestClient):

    def __init__(self, ipaddress, portid, clientid):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)
        self.connect(ipaddress, portid, clientid)
        thread = Thread(target = self.run)
        thread.start()
        setattr(self, "_thread", thread)
        self.init_error()

if __name__ == '__main__':

    ## Check that the port is the same as on the Gateway
    ## ipaddress is 127.0.0.1 if one same machine, clientid is arbitrary

    ## use port 4001 for IB Gateway and 7496 for TWS
    app = TestApp("127.0.0.1", 7496, 10)

    # ES Contract
    ibContract = IBcontract()
    ibContract.secType = "CONTFUT"
    #ibContract.secType = "FUT"
    # for continuous futures, we don't need the below line of code.
    #ibContract.lastTradeDateOrContractMonth="201806"
    ibContract.symbol = "ES"
    ibContract.exchange = "GLOBEX"
    ibContract.currency = "USD"

    # Eurodollar Contract
    #ibContract = IBcontract()
    #ibContract.secType = "FUT"
    #ibContract.lastTradeDateOrContractMonth="201809"
    #ibContract.symbol="ES"
    #ibContract.exchange="GLOBEX"
    #ibContract.currency = "USD"

    # Resolve contract, run the get Hist function
    resolved_ibContract = app.resolve_ibContract(ibContract)
    hist_data = app.getHist(resolved_ibContract)
    print("the type of getHist return data is ", type(hist_data))
    # write out hist_data to a file - just crude write out for now
    with open("C:\\Users\\ghazy\\crude_hist_write.csv", "w")  as f:
        f.write(str(hist_data))
        f.flush()
        f.close()

    ## we can have multiple ( max 32 ) clientId's connected to the server at one time
    ## One can be getting prices, anothing receivng accounting info, another managing
    ## orders, another one getting diagnostic information, etc...
    current_time = app.speaking_clock()
    scanner_params_xml = app.get_scanner_params_as_xml()

    with open("C:\\Users\\ghazy\\IB_Scanner_Params.xml", "w") as f:
        f.write(scanner_params_xml)
        f.flush()
        f.close()
    print("Current time is ", current_time)
    app.disconnect()

