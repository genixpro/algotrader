import pyximport
pyximport.install()

from algotrader import analyzer

def run():
    analyzer.analyzeAllOptions()



if __name__ == '__main__':
    run()
