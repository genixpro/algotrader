import requests
import datetime
import json
import pickle
import os.path
from pprint import pprint


ameritradeAPIKey = "S20BUIA2BJBURHRRWDLIPAUCCUYDELEE"

def getPriceData(symbol):
    queryParams = {
            "apikey": ameritradeAPIKey,
            "periodType": "year",
            "period": 1,
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
            item['datetime'] = datetime.datetime.utcfromtimestamp(item['datetime'] / 1000)
            item['symbol'] = symbol

            yield item


def getOptionChain(symbol, contract):
    now = datetime.datetime.now()
    startOfHour = datetime.datetime(year=now.year, month=now.month, day=now.day, hour=now.hour, minute=0, second=0, microsecond=0)
    cacheFileName = f"cache/options-chain-{symbol}-{contract}-{startOfHour.isoformat()}.bin"

    # TODO: this should use mongo with a TTL index instead of a local file cache
    if os.path.exists(cacheFileName):
        f = open(cacheFileName, 'rb')
        data = pickle.load(f)
        f.close()
        return data
    else:
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
