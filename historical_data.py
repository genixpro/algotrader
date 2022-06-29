import ameritrade
import pymongo

class PriceDatapoint:
    def __init__(self, rawDatapoint=None):
        if rawDatapoint is not None:
            self.open = rawDatapoint['open']
            self.close = rawDatapoint['close']
            self.datetime = rawDatapoint['datetime']
        else:
            self.open = None
            self.close = None
            self.datetime = None

        self.dayChange = None
        self.gapPrevious = None
        self.gapNext = None


class HistoricalPrices:
    def __init__(self):
        self.client = pymongo.MongoClient()
        self.db = self.client['algotrade']

        self.rawPricesCollection = self.db['historical_prices_raw']

        self.rawPricesCollection.create_index(
            [
                ("symbol", pymongo.DESCENDING),
                ("datetime", pymongo.DESCENDING)
            ],
            sparse=True,
            unique=True
        )

    def saveRawDataLocally(self, symbol):
        data = ameritrade.getPriceData(symbol)

        for item in data:
            self.rawPricesCollection.update_one({
                "symbol": symbol,
                "datetime": item['datetime']
            }, {"$set": item}, upsert=True)


    def getRawDataBetweenDates(self, symbol, startDate, endDate):
        items = self.rawPricesCollection.find(
            filter={
                "symbol": symbol,
                "$and": [
                    {"datetime": {"$gte": startDate}},
                    {"datetime": {"$lte": endDate}},
                ]
            },
            sort=[("datetime", pymongo.ASCENDING)]
        )

        return list(items)

    def getFirstRawDatapointAfterDate(self, symbol, date):
        first_item = self.rawPricesCollection.find_one(
            filter={
                "symbol": symbol,
                "$and": [
                    {"datetime": {"$gte": date}}
                ]
            },
            sort=[("datetime", pymongo.ASCENDING)]
        )

        return first_item

    def getProcessedTimeSeriesBetweenDates(self, symbol, startDate, endDate):
        rawDatapoints = self.getRawDataBetweenDates(symbol, startDate, endDate)

        processedDatapoints = []

        for n in range(len(rawDatapoints)):
            rawDatapoint = rawDatapoints[n]
            nextRawDatapoint = None
            lastRawDatapoint = None

            datapoint = PriceDatapoint(rawDatapoint)

            datapoint.dayChange = rawDatapoint['close'] / rawDatapoint['open']

            if n > 0:
                lastRawDatapoint = rawDatapoints[n - 1]
                datapoint.gapPrevious = rawDatapoint['open'] / lastRawDatapoint['close']
            else:
                datapoint.gapPrevious = None

            if n < (len(rawDatapoints) - 1):
                nextRawDatapoint = rawDatapoints[n + 1]
                datapoint.gapNext = nextRawDatapoint['open'] / rawDatapoint['close']
            else:
                datapoint.gapNext = None

            processedDatapoints.append(datapoint)

        return processedDatapoints
