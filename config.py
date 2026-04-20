import os

# Fetching & Lookback (Unified Time Span)
DEFAULT_DAYS_BACK = int(os.getenv("DEFAULT_DAYS_BACK", 3))
DATA_DIR = os.getenv("DATA_DIR", "data")

# Define Competitors, their endpoints, and their structural data logic
COMPETITORS = {
    "News18 Gujarati": {
        "sitemap": "https://gujarati.news18.com/commonfeeds/v1/guj/sitemap-index.xml",
        "fetch_strategy": "daily_index",
        "days_to_fetch": DEFAULT_DAYS_BACK
    },
    "TV9 Gujarati": {
        "sitemap": "https://tv9gujarati.com/news-sitemap.xml",
        "fetch_strategy": "direct",
        "days_to_fetch": DEFAULT_DAYS_BACK
    },
    "ABP Gujarati": {
        "sitemap": "https://gujarati.abplive.com/news-sitemap.xml",
        "fetch_strategy": "daily_index",
        "days_to_fetch": DEFAULT_DAYS_BACK
    },
    "Gujarat Samachar": {
        "sitemap": "https://www.gujaratsamachar.com/sitemap.xml",
        "fetch_strategy": "direct",
        "days_to_fetch": DEFAULT_DAYS_BACK
    },
    "Sandesh": {
        "sitemap": "https://sandesh.com/top-10.xml",
        "fetch_strategy": "direct",
        "days_to_fetch": DEFAULT_DAYS_BACK
    },
    "Zee Gujarati": {
        "sitemap": "https://zeenews.india.com/gujarati/sitemaps/news-sitemap.xml",
        "fetch_strategy": "direct_waf_bypass",
        "days_to_fetch": DEFAULT_DAYS_BACK
    },
    "Divya Bhaskar": {
        "sitemap": "https://www.divyabhaskar.co.in/sitemaps-v1--sitemap-google-news-1.xml",
        "fetch_strategy": "direct",
        "days_to_fetch": DEFAULT_DAYS_BACK
    },
}
# Data storage
JSON_STORE_FILE = os.path.join(DATA_DIR, "news_data.json")
ANALYSIS_STORE_FILE = os.path.join(DATA_DIR, "analysis_results.json")

# Parsing settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2
CHUNK_SIZE = 500  # Process articles in chunks for memory optimization

# NLP settings
MIN_SIMILARITY_THRESHOLD = 0.35
HIGH_SIMILARITY_THRESHOLD = 0.65
TOP_KEYWORDS_COUNT = 20
NGRAM_RANGE = (1, 3)

# Fetching & Lookback
# Controlled globally at the top of the file via DEFAULT_DAYS_BACK
