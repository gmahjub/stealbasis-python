"""
Copyright (C) 2016 Interactive Brokers LLC. All rights reserved.  This code is
subject to the terms and conditions of the IB API Non-Commercial License or the
 IB API Commercial License, as applicable. 
"""

import sys

from ibapi.object_implem import Object 
from ibapi.scanner import ScannerSubscription


class ScannerSubscriptionSamples(Object):

    @staticmethod
    def TopPercentGainerUsEquity1():
        # top percent gainers of stocks with Market Cap > 1B and
        # average volume greater than 100K
        #! [toppercentgainerusequity]
        scanSub = ScannerSubscription()
        scanSub.instrument = "STK"
        scanSub.locationCode = "STK.US.MAJOR"
        scanSub.scanCode = "TOP_PERC_GAIN"
        return scanSub

    @staticmethod
    def TopPercentLoserUsEquity1():
        # top percent losers of stocks with Market Cap < 1B and
        # average volume greater than 100K
        #! [toppercentloserusequity]
        scanSub = ScannerSubscription()
        scanSub.instrument = "STK"
        scanSub.locationCode = "STK.US.MAJOR"
        scanSub.scanCode = "TOP_PERC_LOSER"
        return scanSub

    @staticmethod
    def LowPriceEarningsRatio():
        scanSub = ScannerSubscription()
        scanSub.instrument = "STK"
        scanSub.locationCode = "STK.US.MAJOR"
        scanSub.scanCode = "LOW_PE_RATIO"
        return scanSub

    @staticmethod
    def HighReturnOnEquity():
        scanSub = ScannerSubscription()
        scanSub.instrument = "STK"
        scanSub.locationCode = "STK.US.MAJOR"
        scanSub.scanCode = "HIGH_RETURN_ON_EQUITY"
        return scanSub

    @staticmethod
    def LowReturnOnEquity():
        scanSub = ScannerSubscription()
        scanSub.instrument = "STK"
        scanSub.locationCode = "STK.US.MAJOR"
        scanSub.scanCode = "LOW_RETURN_ON_EQUITY"

    @staticmethod
    def LowPriceTangibleBookRatio():
        scanSub = ScannerSubscription()
        scanSub.instrument = "STK"
        scanSub.locationCode = "STK.US.MAJOR"
        scanSub.scanCode = "LOW_PRICE_2_TAN_BOOK_RATIO"
        return scanSub

    #### Everything below here are sample scanners that came with IB API Samples.

    @staticmethod
    def HotUSStkByVolume():
        #! [hotusvolume]
        #Hot US stocks by volume
        scanSub = ScannerSubscription()
        scanSub.instrument = "STK"
        scanSub.locationCode = "STK.US.MAJOR"
        scanSub.scanCode = "HOT_BY_VOLUME"
        #! [hotusvolume]
        return scanSub

    @staticmethod
    def TopPercentGainersIbis():
        #! [toppercentgaineribis]
        # Top % gainers at IBIS
        scanSub = ScannerSubscription()
        scanSub.instrument = "STOCK.EU"
        scanSub.locationCode = "STK.EU.IBIS"
        scanSub.scanCode = "TOP_PERC_GAIN"
        #! [toppercentgaineribis]
        return scanSub

    @staticmethod
    def MostActiveFutSoffex():
        #! [mostactivefutsoffex]
        # Most active futures at SOFFEX
        scanSub = ScannerSubscription()
        scanSub.instrument = "FUT.EU"
        scanSub.locationCode = "FUT.EU.SOFFEX"
        scanSub.scanCode = "MOST_ACTIVE"
        #! [mostactivefutsoffex]
        return scanSub

    @staticmethod
    def HighOptVolumePCRatioUSIndexes():
        #! [highoptvolume]
        # High option volume P/C ratio US indexes
        scanSub = ScannerSubscription()
        scanSub.instrument = "IND.US"
        scanSub.locationCode = "IND.US"
        scanSub.scanCode = "HIGH_OPT_VOLUME_PUT_CALL_RATIO"
        #! [highoptvolume]
        return scanSub

def Test():
    print(ScannerSubscriptionSamples.HotUSStkByVolume())
    print(ScannerSubscriptionSamples.TopPercentGainersIbis())
    print(ScannerSubscriptionSamples.MostActiveFutSoffex())
    print(ScannerSubscriptionSamples.HighOptVolumePCRatioUSIndexes())
    
 
if "__main__" == __name__:
    print("Run test in ScannerSubscription Samples...")
    Test()
 
