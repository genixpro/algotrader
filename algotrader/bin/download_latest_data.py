import pyximport
pyximport.install()

from algotrader import constants
from algotrader import historical_data

def run():
    for symbol in constants.symbolsToTrade:
        print(f"Downloading historical data for {symbol}")
        historicals = historical_data.HistoricalPrices()
        historicals.saveRawDataLocally(symbol)



if __name__ == '__main__':
    run()
