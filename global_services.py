import concurrent.futures
import constants

globalExecutor = concurrent.futures.ProcessPoolExecutor(max_workers=constants.numWorkers)
