from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_RAW = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "risk.db"
OUT = ROOT / "outputs"

START = "2015-01-01"
END = "2025-12-31"

INDEX_TICKER = "SPY"

# ticker: (name, sector). add or remove rows here and rerun the pipeline
UNIVERSE = {
    "AAPL": ("Apple", "Technology"),
    "MSFT": ("Microsoft", "Technology"),
    "NVDA": ("Nvidia", "Technology"),
    "AVGO": ("Broadcom", "Technology"),
    "ORCL": ("Oracle", "Technology"),
    "GOOGL": ("Alphabet", "Communication"),
    "NFLX": ("Netflix", "Communication"),
    "DIS": ("Walt Disney", "Communication"),
    "VZ": ("Verizon", "Communication"),
    "T": ("AT&T", "Communication"),
    "JPM": ("JPMorgan Chase", "Financials"),
    "BAC": ("Bank of America", "Financials"),
    "WFC": ("Wells Fargo", "Financials"),
    "GS": ("Goldman Sachs", "Financials"),
    "MS": ("Morgan Stanley", "Financials"),
    "BRK-B": ("Berkshire Hathaway", "Financials"),
    "JNJ": ("Johnson & Johnson", "Health Care"),
    "UNH": ("UnitedHealth", "Health Care"),
    "PFE": ("Pfizer", "Health Care"),
    "LLY": ("Eli Lilly", "Health Care"),
    "MRK": ("Merck", "Health Care"),
    "ABBV": ("AbbVie", "Health Care"),
    "AMZN": ("Amazon", "Consumer Discretionary"),
    "TSLA": ("Tesla", "Consumer Discretionary"),
    "HD": ("Home Depot", "Consumer Discretionary"),
    "MCD": ("McDonald's", "Consumer Discretionary"),
    "NKE": ("Nike", "Consumer Discretionary"),
    "PG": ("Procter & Gamble", "Consumer Staples"),
    "KO": ("Coca-Cola", "Consumer Staples"),
    "PEP": ("PepsiCo", "Consumer Staples"),
    "WMT": ("Walmart", "Consumer Staples"),
    "COST": ("Costco", "Consumer Staples"),
    "XOM": ("Exxon Mobil", "Energy"),
    "CVX": ("Chevron", "Energy"),
    "COP": ("ConocoPhillips", "Energy"),
    "SLB": ("Schlumberger", "Energy"),
    "CAT": ("Caterpillar", "Industrials"),
    "BA": ("Boeing", "Industrials"),
    "GE": ("GE Aerospace", "Industrials"),
    "UPS": ("UPS", "Industrials"),
    "HON": ("Honeywell", "Industrials"),
    "NEE": ("NextEra Energy", "Utilities"),
    "DUK": ("Duke Energy", "Utilities"),
    "SO": ("Southern Company", "Utilities"),
    "LIN": ("Linde", "Materials"),
    "SHW": ("Sherwin-Williams", "Materials"),
    "PLD": ("Prologis", "Real Estate"),
    "AMT": ("American Tower", "Real Estate"),
}
INDEX_ROW = {"SPY": ("SPDR S&P 500 ETF", "Index")}

# the 10 names used in the excel portfolio
PORTFOLIO = ["AAPL", "MSFT", "JPM", "JNJ", "XOM", "PG", "AMZN", "NEE", "CAT", "VZ"]

FRED_SERIES = ["VIXCLS", "DGS10", "FEDFUNDS"]
