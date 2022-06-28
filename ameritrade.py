import requests
import datetime
import json
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
    return data
