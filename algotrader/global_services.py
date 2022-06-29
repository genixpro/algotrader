import concurrent.futures
from algotrader import constants

globalExecutor = concurrent.futures.ProcessPoolExecutor(max_workers=constants.numWorkers)
