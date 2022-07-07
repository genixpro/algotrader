import pyximport
pyximport.install()

from algotrader import constants
from algotrader import historical_data
import time

def run():
    for symbol in constants.symbolsToTrade:
        print(f"Downloading historical data for {symbol}")
        historicals = historical_data.HistoricalPrices()
        historicals.saveRawDataLocally(symbol)
        time.sleep(0.5)



if __name__ == '__main__':
    run()
