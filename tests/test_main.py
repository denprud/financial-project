import pytest
import sys
import pandas as pd
sys.path.append("..")
from src.appTwo import isRsiOptimal, fibonacci_retracement, getVolume, getRangesLower, getRangesHigher, isPricePollingFinished, fib_get_low_high, fib_get_bands


class Tests:
    
    def test_RsiOptimalTest(self):
        isRsiGood = isRsiOptimal("NVDA")
        assert isinstance(isRsiGood, bool)
    
    def test_getVolume(self):
        volumeScore = getVolume("NVDA")
        assert isinstance(volumeScore, float)
    
    def test_getRangesLower(self):
        for x in range(0, 80, 10):
            volumeScore =  getRangesLower(x)
            assert isinstance(volumeScore, float)
    
    def test_getRangesHigher(self):
        for x in range(0, 80, 10):
            volumeScore =  getRangesHigher(x)
            assert isinstance(volumeScore, float)

    def test_fibonacci_retracement(self):
        priceStats = fibonacci_retracement("NVDA")
        assert priceStats is not None
        assert priceStats["lowerBand"] is not None
        assert priceStats["oneThirdPercentAbove"] is not None
        assert priceStats["oneThirdPercentBelow"] is not None
        assert priceStats["twoThirdPercentAbove"] is not None
        assert priceStats["twoThirdPercentBelow"] is not None

    def test_fib_get_low_high(self):
        df = pd.read_csv('out.csv')
        high,low = fib_get_low_high(df)
        assert int(high) == int(1154.92)
        assert int(low) == int(756.06)
    
    def test_fibonacci_retracement_ranges(self):
        df = pd.read_csv('out.csv')
        high,low = fib_get_low_high(df)
        price = df['Close'].iloc[-1]
        priceStats = fib_get_bands(price=price, high=high, low=low)
        assert priceStats["fibInterval"] == high-low
        assert int(priceStats["upperBand"]) == int(high)
        assert int(priceStats["lowerBand"]) == int(high - 0.786 * priceStats["fibInterval"])
        assert priceStats["oneThirdPercentAbove"] == 0.07788
        assert priceStats["oneThirdPercentBelow"] ==  0.03894
        assert priceStats["twoThirdPercentAbove"] == 0.15576
        assert priceStats["twoThirdPercentBelow"] == 0.07788

    def test_isPricePollingFinished(self):
        df = pd.read_csv('out.csv')
        high,low = fib_get_low_high(df)
        price = df['Close'].iloc[-1]
        priceStats = fib_get_bands(price=price, high=high, low=low)
        print(f"gfctcfhg:{priceStats["upperBand"]}")
        print(f"gfctcfhg:{priceStats["lowerBand"]}")
        print(f"price:{price}")
        volumeScore = getVolume("NVDA")
        isPriceFinished, sentiment = isPricePollingFinished(data=df,priceStats=priceStats,isRecentlyUnderBound=True,volumeScore=volumeScore)
        assert sentiment == "N/A"
        assert isPriceFinished == False
        df2 = pd.read_csv('out2.csv')
        isPriceFinished, sentiment = isPricePollingFinished(data=df2,priceStats=priceStats,isRecentlyUnderBound=True,volumeScore=volumeScore)
        assert sentiment == "Buy"
        assert isPriceFinished == True
        df3 = pd.read_csv('out3.csv')
        isPriceFinished, sentiment = isPricePollingFinished(data=df3,priceStats=priceStats,isRecentlyUnderBound=True,volumeScore=volumeScore)
        assert sentiment == "Disband"
        assert isPriceFinished == True
        isPriceFinished, sentiment = isPricePollingFinished(data=df3,priceStats=priceStats,isRecentlyUnderBound=False,volumeScore=volumeScore)
        assert sentiment == "Sell"
        assert isPriceFinished == True
        
        

        
    
