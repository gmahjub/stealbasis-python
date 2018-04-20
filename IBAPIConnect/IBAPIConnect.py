from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from threading import Thread
import queue

class TestWrapper(EWrapper):
    """
    The wrapper deals with the action coming back from the IB gateway or TWS instance

    We override methods in EWrapper that will get called when this action happens, like currentTime


    """

    ## error handling code
    def init_error(self):
        error_queue=queue.Queue()
        self._my_errors = error_queue

    def get_error(self, timeout=5):
        if self.is_error():
            try:
                return self._my_errors.get(timeout=timeout)
            except queue.Empty:
                return None

        return None

    def is_error(self):
        an_error_if=not self._my_errors.empty()
        return an_error_if

    def error(self, id, errorCode, errorString):
        ## Overriden method
        errormsg = "IB error id %d errorcode %d string %s" % (id, errorCode, errorString)
        self._my_errors.put(errormsg)

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

    ## we can have multiple ( max 32 ) clientId's connected to the server at one time
    ## One can be getting prices, anothing receivng accounting info, another managing
    ## orders, another one getting diagnostic information, etc...

    current_time = app.speaking_clock()
    scanner_params_xml = app.get_scanner_params_as_xml()

    with open("C:\\Users\\ghazy\\IB_Scanner_Params.xml", "w") as f:
        f.write(scanner_params_xml)
        f.flush()
        f.close()
        
    print(current_time)
    #print(scanner_params_xml)

    app.disconnect()

