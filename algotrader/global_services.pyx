import pyximport
pyximport.install()

import concurrent.futures
from algotrader import constants

globalExecutor = concurrent.futures.ProcessPoolExecutor(max_workers=constants.numWorkers)
# globalExecutor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
