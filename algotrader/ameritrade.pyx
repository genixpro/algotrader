# cython: language_level=3, boundscheck=True
import pyximport
pyximport.install()

import requests
import datetime
import json
import pickle
import os.path
from algotrader import constants
from pprint import pprint


ameritradeAPIKey = "S20BUIA2BJBURHRRWDLIPAUCCUYDELEE"

def getPriceData(symbol):
    startDate = datetime.datetime.now() - datetime.timedelta(days=365)
    endDate = datetime.datetime.now() + datetime.timedelta(days=1)

    queryParams = {
            "apikey": ameritradeAPIKey,
            "periodType": "year",
            "startDate": round(startDate.timestamp() * 1000),
            "endDate": round(endDate.timestamp() * 1000),
            "frequencyType": "daily",
            "frequency": "1",
        }

    response = requests.get(
        url=f"https://api.tdameritrade.com/v1/marketdata/{symbol}/pricehistory",
        params=queryParams
    )

    data = json.loads(response.content)

    if 'candles' not in data:
        pprint(data)
        raise Exception("Error fetching data from Ameritrade")
    else:
        for item in data['candles']:
            dateObject = datetime.datetime.utcfromtimestamp(item['datetime'] / 1000)
            dateObject = dateObject.replace(hour=0, minute=0, second=0, microsecond=0)
            item['datetime'] = dateObject
            item['symbol'] = symbol

            yield item


def getOptionChain(symbol, contract):
    now = datetime.datetime.now()
    startOfHour = datetime.datetime(year=now.year, month=now.month, day=now.day, hour=now.hour, minute=0, second=0, microsecond=0)

    if not os.path.exists("cache"):
        os.mkdir("cache")

    # TODO: this should use mongo with a TTL index instead of a local file cache
    cacheFileName = f"cache/options-chain-{symbol}-{contract}-{startOfHour.isoformat()}.bin"
    if os.path.exists(cacheFileName):
        if constants.verboseOutput:
            print(f"Using cached options quotes from file {cacheFileName}")
        f = open(cacheFileName, 'rb')
        data = pickle.load(f)
        f.close()
        return data
    else:
        if constants.verboseOutput:
            print(f"Fetching fresh options quotes from Ameritrade")

        response = requests.get(
            url=f"https://api.tdameritrade.com/v1/marketdata/chains",
            params={
                "apikey": ameritradeAPIKey,
                "symbol": symbol,
                "contractType": contract,
                "strikeCount": 25,
                "includeQuotes": "FALSE",
            }
        )

        data = json.loads(response.content)

        f = open(cacheFileName, 'wb')
        pickle.dump(data, f)
        f.close()

        return data
