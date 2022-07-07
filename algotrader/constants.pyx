# cython: language_level=3, boundscheck=True
import multiprocessing

numWorkers = multiprocessing.cpu_count() + 1

priceSimulationTradingDaysOfHistoricalDataToUse = 120
priceSimulationNumberOfSimulations = 100000

investmentSimulationConsecutiveTrades = 25
investmentSimulationNumberOfSimulations = 1000
# investmentSimulationNumberOfSimulations = 10000
investmentSimulationOutlierProportionToDiscard = 0.001

optionPriceIncrement = 0.5
optionChainStartPriceRatio = 0.5
optionChainEndPriceRatio = 2.0
optionClearingPriceSpreadMidpoint = 0.7
optionMinExpirationTimeDays = 4
optionMaxExpirationTimeDays = 25

correlationAnalysisMovingAveragePeriodDays = 8

verboseOutput = False
generateCharts = False

techStocks = [
    "HOOD",
    "COIN",
    "AAPL",
    "MSFT",
    "GOOG",
    "AMZN",
    "TSLA",
    "META",
    "NVDA",
    "AVGO",
    "ASML",
    "ORCL",
    "CSCO",
    "ADBE",
    "CRM",
    "INTC",
    "QCOM",
    "TXN",
    "AMD",
    "IBM",
    "SAP",
    "INTU",
    "SONY",
    "NOW",
    "PYPL",
    "AMAT",
    "NFLX",
    "BKNG",
    "ADI",
    "MU",
    "ABNB",
    # "ATVI", # Removing activision blizzard because they are going through an acquisition, which makes things unpredictable
    "VMW",
    "PANW",
    "TEAM",
    "SNOW",
    "SHOP",
    "UBER",
    "ROP",
    "NXPI",
    "CRWD",
    "ADSK",
    "WDAY",
    "SQ",
    "DELL",
    "HPQ",
    "EA",
    "ZM",
    "VEEV",
    "ANET",
    "TWTR",
    "DDOG",
    "STM",
    "NOK",
    "ERIC",
    "GPN",
    "MCHP"
]

funds = [
    "MGC", # Vanguard megacap (all large companies)
    "XLB", # Materials
    "XLE", # Energy
    "XLC", # Communications
    "XLY", # Consumer Discretionary
    # "XLP", # Consumer Staples
    # "XLF", # Financial
    "XLV", # Healthcare
    # "XLI", # Industrial
    # "IFRA", # Infrastructure
    "XLK", # Tech
    "XLU", # Utitilies
]


commodity = [
    "IAU", # Gold
    "SLV", # Silver,
    "USO", # Oil
    "UCO", # Crude oil
    "PPLT", # Platinum
    "WEAT", # Wheat - high expense, hopefully can find better
    "DBB", # Base metals
    "PALL", # Palladium
    "CORN", # Corn
    "CPER", # Copper
    "SOYB", # Soybeans
    "CANE",  # Sugar
    "BAL", # Cotton
    "DBA", # Agriculture, broad
]

realEstate = [
    "LAND", # Farm
    "BXP", # Office
    "PLD", # Industrial
    "CPT", # Apartment
    "MAA", # Apartment
]

bonds = [
    "BLV", # Long term USA
    "BSV", # Short term USA
    "SPIB", # Long term corporate USA
    "SPHY", # High yield bonds
]

international = [
    "VWOB", # Emerging market bonds
    "SCHE", # Emerging market stock
    "VPL", # Pacific asia
    "VGK", # Europe
    "VT", # Total world
]

financial = [
    "JPM", # JP morgan chase
    "BAC", # Bank of america
    "WFC", #wells fargo
    "RY", # RBC canada
    "MS", # Morgan stanley
    "HSBC", # HSBC
    "SCHW", # Charles Schwab
    "TD", # Toronto dominion bank
]

energy = [
    "XOM", # Exxon Mobil
    "CVX", # Chevron
    # "RDS.A", # Royal dutch
    "TTE", # Total energies
    "COP", # Conoco phillips
    "BP", # British petroleum
    "EQNR", # Equinor
    "ENB", # Enbridge
    "CNQ", # Canadian natural resources
]

manufacturing = [
    "AZN", # Astra Zeneca
    "SNY", # Sanofi
    "WOLF", # Wolfspeed
    "VC", # Visteon
]

retail = [
    "WMT", # Walmart
    "HD", # Home depot
    "COST", # Costco
    "CVS", # CVS Pharmacy
    "LOW", # Lowes
    "TGT", # Target
    "DLTR", # Dollar Tree
    "AZO", # Auto Zone
    "KR", # Kroger
]

consumer = [
    "PG", # Procter & Gamble
    "PM", # Phillip Morris
    "UL", # Unilever
    "EL", # Estee Lauder
    "CL", # Colgate Palmolive
]

food = [
    "HSY", # Hershey
    "KO", # Coca cola
    "PEP", # Pepsico
    "BUD", # Anhauser busch
    "DEO", # Diageo
    "MDLZ", # Mondelez International
    "MNST", # Monster Beverage
    "KDP", # Dr Pepper
    "KHC", # Kraft Heinz
]

symbolsToTrade = techStocks + funds + commodity + realEstate + bonds + \
                 international + financial + energy + manufacturing + retail + \
                 consumer + food

symbolsToTrade = funds