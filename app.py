# -*- coding: utf-8 -*-
"""
Breaking News Finder - Streamlit Dashboard
Zee Gujarati Competitor Analysis Tool
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import COMPETITORS, DEFAULT_DAYS_BACK
from sitemap_parser import fetch_all_competitors
from nlp_engine import NewsAnalyzer, run_full_analysis
from data_store import save_articles, load_articles, save_analysis, load_analysis, get_data_freshness

st.set_page_config(
    page_title="Breaking News Finder | Zee Gujarati",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGE_LATEST = "🏠 Dashboard"
PAGE_COVERAGE = "🏁 Coverage Race"
PAGE_DUPLICATES = "🔥 Duplicate Content"
PAGE_DATE_WISE = "📊 Raw Data"

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');

    :root {
        --primary: #FF4B4B;
        --secondary: #262730;
        --bg-dark: #0D1117;
        --sidebar-bg: #0e1117;
        --text-main: #FAFAFA;
        --text-dim: #94A3B8;
        --card-bg: #161B22;
        --card-border: #30363D;
        --status-bg: #0C1821;
        --status-border: #1A3A4A;
        --status-text: #00BFFF;
    }



    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif !important;
        background-color: var(--bg-dark);
        color: var(--text-main);
    }

    /* Global Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-dark);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--card-border);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary);
    }

    /* Fix White Table Issue - Large Dataset Glide Grid Fix */
    div[data-testid="stDataFrame"], 
    div.stDataFrame,
    div[data-testid="stDataFrame"] [data-testid="stTable"] {
        background-color: var(--card-bg) !important;
    }

    /* Force the internal Glide components to show the background */
    div[data-testid="stDataFrame"] [role="grid"],
    div[data-testid="stDataFrame"] [role="presentation"] {
        background-color: var(--card-bg) !important;
    }

    /* Target the actual host element of the Glide Grid for large datasets */
    div[data-testid="stDataFrame"] > div:first-child {
        background-color: var(--card-bg) !important;
    }
    
    /* Ensure the wrapper doesn't have a white background */
    /* Dataframe Inner Styling */
    .stDataFrame [data-testid="stTable"] {
        background-color: var(--card-bg) !important;
    }

    /* Professional Table Refinement */
    [data-testid="stDataFrame"], .stDataFrame, table {
        font-size: 1.4rem !important;
    }
    
    [data-testid="stDataFrame"] th, th {
        font-size: 1.3rem !important;
        font-weight: 700 !important;
    }




    /* Sidebar Styling - YT Recommender Dark */
    [data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    
    /* Soften sidebar content for the fade effect */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
        opacity: 0.7;
    }

    
    /* Slightly fade the labels within the sidebar for a sophisticated look */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        opacity: 0.85;
    }




    /* Remove gap above News Finder */
    [data-testid="stSidebar"] section[data-testid="stSidebarContent"] > div {
        padding-top: 0px !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1 {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: var(--primary) !important;
        display: flex;
        justify-content: center;
        align-items: center;
        text-align: center;
        gap: 10px;
        margin-bottom: 0px !important;
        letter-spacing: -0.5px;
    }

    [data-testid="stSidebar"] .stCaption {
        color: #808495;
        font-size: 0.85rem !important;
        font-weight: 500;
        margin-bottom: 1.5rem !important;
    }

    /* Status Box Style */
    .status-box {
        background: var(--status-bg);
        border: 1px solid var(--status-border);
        border-radius: 8px;
        padding: 5px 12px;
        color: var(--status-text);
        font-size: 0.75rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }

    /* Ultra-Compact Radio Navigation */
    div[data-testid="stRadio"] > div {
        gap: 0px !important;
        padding: 0px !important;
    }
    
    div[data-testid="stRadio"] label {
        background: transparent !important;
        border-radius: 4px !important;
        padding: 2px 10px !important;
        transition: all 0.2s ease;
        border: 1px solid transparent !important;
        margin-bottom: 0px !important;
        cursor: pointer;
        display: flex !important;
        align-items: center;
    }

    div[data-testid="stRadio"] label:hover {
        background: rgba(255, 255, 255, 0.05) !important;
    }

    /* Active Radio Item */
    div[data-testid="stRadio"] label:has(input:checked) {
        background: rgba(255, 75, 75, 0.1) !important;
        border-left: 3px solid var(--primary) !important;
        color: var(--primary) !important;
    }

    div[data-testid="stRadio"] label p {
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        color: inherit !important;
        margin: 0 !important;
    }

    /* Hide the radio circle and its container */
    div[data-testid="stRadio"] input, 
    div[data-testid="stRadio"] div[role="radiogroup"] div[data-testid="stMarkdownContainer"] ~ div {
        display: none !important;
    }
    
    /* Re-show the label text */
    div[data-testid="stRadio"] label p {
        display: block !important;
    }
    
    /* Primary Button Styling - RED */
    .stButton > button[kind="primary"] {
        width: 100%;
        background: linear-gradient(135deg, var(--primary), #FF1F1F) !important;
        color: white !important;
        border: none !important;
        padding: 0.45rem 0.6rem !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.2);
    }

    /* Secondary Button Styling - GLASS/DARK */
    .stButton > button[kind="secondary"] {
        width: 100%;
        background: rgba(255, 255, 255, 0.05) !important;
        color: var(--text-main) !important;
        border: 1px solid var(--card-border) !important;
        padding: 0.45rem 0.6rem !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
    }

    /* Load Cached Data - Teal Blue */
    .load-btn-wrap .stButton > button {
        background: linear-gradient(135deg, #1a6b8a, #0e4d6b) !important;
        color: white !important;
        border: none !important;
        padding: 0.45rem 0.6rem !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 12px rgba(26, 107, 138, 0.3) !important;
    }
    .load-btn-wrap .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(26, 107, 138, 0.4) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 255, 255, 0.05);
    }


    /* Glassmorphism Stat Cards */
    .stat-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        border-color: var(--primary);
        box-shadow: 0 8px 24px rgba(255, 75, 75, 0.1);
    }

    .stat-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: var(--primary);
        line-height: 1.2;
    }

    .stat-label {
        font-size: 0.85rem !important;
        color: var(--text-dim);
        font-weight: 500;
        margin-top: 5px;
    }


    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid var(--card-border);
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        color: var(--text-dim) !important;
        font-weight: 600 !important;
        font-size: 1.2rem !important;
        background-color: transparent !important;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        color: var(--primary) !important;
        border-bottom: 3px solid var(--primary) !important;
    }

    /* Target the tab content specifically */
    [data-baseweb="tab-panel"], [data-testid="stTab"] {
        background-color: transparent !important;
        border: none !important;
    }


    /* Custom Warning Card */
    .warning-card {
        background: rgba(255, 75, 75, 0.05);
        border: 1px solid rgba(255, 75, 75, 0.2);
        border-radius: 12px;
        padding: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 1rem 0;
    }

    /* Section Titles - YT Recommender Style */
    .section-title {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 4px;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .section-subtitle {
        font-size: 0.95rem;
        color: #8B949E;
        margin-bottom: 25px;
        font-weight: 400;
    }

    /* Hide default streamlit elements */
    header { visibility: hidden !important; }
    footer { visibility: hidden !important; }
    #MainMenu { visibility: hidden !important; }

    /* Custom Separator */
    .custom-hr {
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--card-border), transparent);
        margin: 1rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


from functools import lru_cache

def format_time_gap(seconds):
    if seconds == 0:
        return "🚀 First!"
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hrs > 0:
        return f"+{hrs}h {mins}m {secs}s"
    elif mins > 0:
        return f"+{mins}m {secs}s"
    else:
        return f"+{secs}s"


@lru_cache(maxsize=4096)
def parse_ts(pub_str):
    if not pub_str:
        return None
    try:
        ts = pd.to_datetime(pub_str)
        if pd.isna(ts):
            return None
        return ts
    except Exception:
        return None


def render_frontend_table(df, key, column_config=None, filename="data.csv", hide_controls=False):
    # ---- SESSION STATE ----
    search_key = f"{key}_search"
    view_key = f"{key}_view"
    
    if search_key not in st.session_state:
        st.session_state[search_key] = ""
    if view_key not in st.session_state:
        st.session_state[view_key] = "table"

    # ---- SEARCH FILTER ----
    filtered_df = df.copy()
    if st.session_state[search_key]:
        query = st.session_state[search_key].lower()
        # Vectorized search is faster than apply(lambda)
        mask = df.astype(str).apply(lambda x: x.str.lower().str.contains(query, na=False)).any(axis=1)
        filtered_df = df[mask]


    # ---- CONTROLS ----
    if not hide_controls:
        col1, col2 = st.columns([6, 1])
        with col2:
            # Only generate CSV if needed or cache it. 
            # Generating on every run is expensive.
            if len(filtered_df) > 0:
                @st.cache_data(ttl=600)
                def convert_df(df_to_save):
                    return df_to_save.to_csv(index=False).encode('utf-8')
                
                csv_data = convert_df(filtered_df)
                st.download_button(
                    label="CSV",
                    data=csv_data,
                    file_name=filename,
                    mime='text/csv',
                    use_container_width=True,
                    key=f"{key}_dl"
                )


    # ---- TABLE RENDERING ----
    row_height = 60
    calculated_height = (len(filtered_df) + 1) * row_height + 60



    dynamic_height = min(calculated_height, 600)
    if dynamic_height < 200: dynamic_height = 200

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        key=key,
        height=dynamic_height,
    )




def get_filters(key_prefix, include_hours=False):
    import datetime
    
    filter_key = f"{key_prefix}_filter_state"
    if filter_key not in st.session_state:
        st.session_state[filter_key] = {"date": datetime.date.today(), "source": "All", "min": 60}
    
    with st.expander("🔍 Filters & Tools", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            today = datetime.date.today()
            date_range = st.date_input(
                "Date Range", 
                value=(today, today), 
                max_value=today,
                key=f"{key_prefix}_date"
            )
            if isinstance(date_range, datetime.date) and not isinstance(date_range, tuple):
                date_range = (date_range, date_range)
            elif isinstance(date_range, (list, tuple)) and len(date_range) == 1:
                date_range = (date_range[0], date_range[0])

        with col2:
            all_sources = ["All"] + list(COMPETITORS.keys())
            source = st.selectbox("Source", all_sources, key=f"{key_prefix}_source")
        with col3:
            if include_hours:
                lookback = st.number_input("Last - Min", min_value=1, max_value=1440, value=60, key=f"{key_prefix}_min")
            else:
                lookback = 60
    
    if include_hours:
        return date_range, source, lookback
    return date_range, source



# ---- SIDEBAR REFINED COMPOSITION ----
with st.sidebar:
    st.markdown("# News Finder")
    
    # Placeholder container for Status/Range (to appear after title)
    status_range_container = st.container()
    
    st.markdown('<hr class="custom-hr">', unsafe_allow_html=True)
    
    page = st.radio(
        "Navigation",
        [PAGE_COVERAGE, PAGE_DUPLICATES, PAGE_DATE_WISE, PAGE_LATEST],
        label_visibility="collapsed",
    )
    
    st.markdown('<hr class="custom-hr">', unsafe_allow_html=True)
    
    fetch_btn = st.button("Fetch Fresh Data", use_container_width=True, type="primary")
    st.markdown('<div class="load-btn-wrap">', unsafe_allow_html=True)
    load_btn = st.button("Load Cached Data", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ---- DATA INITIALIZATION ----
@st.cache_data(ttl=3600, show_spinner=False)
def get_parsed_articles(articles):
    parsed = []
    for a in articles:
        ts = parse_ts(a.get("published_at"))
        parsed.append({
            "article": a,
            "ts": ts,
            "date": ts.date() if ts else None,
        })
    return parsed

if fetch_btn:
    with st.status("🚀 Processing Competitor Scans...", expanded=True) as status:
        all_articles = fetch_all_competitors(hours=DEFAULT_DAYS_BACK * 24)
        if all_articles:
            save_articles(all_articles)
            analysis = run_full_analysis(all_articles)
            save_analysis(analysis)
            st.session_state.articles = all_articles
            st.session_state.analysis = analysis
            st.session_state.parsed_articles = get_parsed_articles(all_articles)
            status.update(label=f"✅ Analysis Complete ({len(all_articles)} items)", state="complete")
        else:
            status.update(label="⚠️ No news found", state="error")

if load_btn or ("articles" not in st.session_state):
    arts = load_articles()
    if arts:
        st.session_state.articles = arts
        st.session_state.analysis = load_analysis()
        st.session_state.parsed_articles = get_parsed_articles(arts)
        if load_btn: st.success(f"Loaded {len(arts)} entries")

articles = st.session_state.get("articles", [])
analysis = st.session_state.get("analysis", {})
parsed_articles = st.session_state.get("parsed_articles", [])


with status_range_container:
    # -- SEPARATE STATUS CARDS --
    freshness = get_data_freshness()
    if freshness:

        try:
            dt_utc = pd.to_datetime(freshness, utc=True)
            now_utc = pd.Timestamp.now(tz="UTC")
            diff = now_utc - dt_utc
            seconds = int(diff.total_seconds())
            if seconds < 60: time_str = "Now"
            elif seconds < 3600: time_str = f"{seconds // 60}m"
            elif seconds < 86400: time_str = f"{seconds // 3600}h"
            else: time_str = f"{seconds // 86400}d"
            
            st.markdown(f'''
                <div style="font-size: 0.9rem; color: #FF4B4B; background: rgba(255, 255, 255, 0.05); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(255, 75, 75, 0.3); font-weight: 700; margin-bottom: 10px; text-align: center;">
                    ⚡ Updated: {time_str} ago
                </div>
            ''', unsafe_allow_html=True)
        except: pass
            
    if articles:
        ts_list = [pa["ts"] for pa in parsed_articles if pa["ts"]]
        if ts_list:
            min_ts, max_ts = min(ts_list), max(ts_list)
            st.markdown(f'''
                <div style="font-size: 0.85rem; color: #FF4B4B; background: rgba(255, 255, 255, 0.05); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(255, 75, 75, 0.3); font-weight: 700; text-align: center;">
                    📅 {min_ts.strftime('%d %b %#I:%M%p').lower()} - {max_ts.strftime('%d %b %#I:%M%p').lower()}
                </div>
            ''', unsafe_allow_html=True)











if not articles:
    st.markdown('<div style="text-align:center; padding:150px 20px;"><div style="font-size:6rem; margin-bottom:32px;">📡</div><h3>Initialize Dataset</h3><p>Click Fetch or Load to begin.</p></div>', unsafe_allow_html=True)
    st.stop()


if page == PAGE_COVERAGE:
    st.markdown('<div class="section-title">🏁 Coverage Race</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Real-time delta analysis between competitor publications.</div>', unsafe_allow_html=True)

    local_date_range, local_source = get_filters("coverage")

    st.markdown("---")

    topic_query = st.text_input(
        "🔎 Search (Title, URL, Keywords)",
        placeholder="Type keyword to search across titles, URLs, or metadata...",
        key="coverage_query",
    )

    cov_start, cov_end = local_date_range if (local_date_range and len(local_date_range) == 2) else (None, None)

    if not topic_query:
        st.markdown(
            """<div style="text-align:center;padding:60px 20px;color:#5e5e78;">
            <div style="font-size:3rem;margin-bottom:12px;">🏁</div>
            <p>Enter a topic keyword above to see which competitors covered it first</p>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        query_tokens = set(re.sub(r"[^\w\s]", " ", topic_query.lower()).split())

        matched = []
        for pa in parsed_articles:
            a = pa["article"]
            ts = pa["ts"]
            if not ts:
                continue
            pub_date = ts.date()
            if cov_start and cov_end and not (cov_start <= pub_date <= cov_end):
                continue

            if local_source != "All" and a.get("source") != local_source:
                continue

            title_text = a.get("title", "").lower()
            keywords_text = a.get("keywords", "").lower()
            url_text = a.get("url", "").lower()
            
            matches_all = True
            for tok in query_tokens:
                if tok.isalnum():
                    pattern = rf"\b{re.escape(tok)}\b"
                    if not (re.search(pattern, title_text) or re.search(pattern, keywords_text) or re.search(pattern, url_text)):
                        matches_all = False
                        break
                else:
                    if tok not in title_text and tok not in keywords_text and tok not in url_text:
                        matches_all = False
                        break
            
            if matches_all:
                matched.append(a)

        if not matched:
            st.warning(f'No articles found for **"{topic_query}"** in the selected date range.')
        else:
            matched.sort(key=lambda x: x.get("published_at", ""))

            first_ts = parse_ts(matched[0].get("published_at", ""))
            first_source = matched[0].get("source", "Unknown")

            st.success(f'Found **{len(matched)}** articles covering **"{topic_query}"** — '
                       f'First reported by **{first_source}** at `{first_ts.strftime("%Y-%m-%d %H:%M") if first_ts else "N/A"}`')

            st.markdown("---")

            st.markdown("### 🥇 Competitor Speed Podium")
            channel_first = {}
            channel_story_count = {}
            for a in matched:
                ch = a.get("source", "Unknown")
                channel_story_count[ch] = channel_story_count.get(ch, 0) + 1
                if ch not in channel_first:
                    channel_first[ch] = a

            podium_list = sorted(channel_first.items(), key=lambda x: x[1].get("published_at", ""))

            medal_colors = ["#FFD700", "#C0C0C0", "#CD7F32"]
            medal_icons = ["🥇", "🥈", "🥉"]

            cols_per_row = 4
            num_channels = len(podium_list)
            
            for i in range(0, num_channels, cols_per_row):
                row_channels = podium_list[i:i + cols_per_row]
                row_cols = st.columns(cols_per_row, gap="large")
                
                for idx, (ch, a) in enumerate(row_channels):
                    total_idx = i + idx
                    ts = parse_ts(a.get("published_at", ""))
                    delay_seconds = (ts - first_ts).total_seconds() if ts and first_ts else 0
                    
                    medal_color = medal_colors[total_idx] if total_idx < 3 else "#2d2d3d"
                    medal_icon = medal_icons[total_idx] if total_idx < 3 else "📺"
                    
                    with row_cols[idx]:
                        story_count = channel_story_count.get(ch, 0)
                        st.markdown(
                            f"""<div class="stat-card" style="border-color:{medal_color}; border-width:2px; height:100%; padding: 18px; margin-bottom: 20px;">
                                <div class="stat-value" style="font-size:1.8rem;">{medal_icon}</div>
                                <div class="stat-label" style="color:var(--primary); font-size:1rem; font-weight:800; margin-top:8px;">{ch}</div>
                                <div class="stat-label" style="font-size:0.8rem; margin-top:4px;">{ts.strftime('%H:%M, %d %b') if ts else 'N/A'}</div>
                                <div class="stat-label" style="font-size:0.85rem; font-weight:700; color:var(--text-main);">{format_time_gap(delay_seconds)}</div>
                                <div class="stat-label" style="font-size:0.8rem; opacity:0.8;">📰 {story_count} stories</div>
                            </div>""",
                            unsafe_allow_html=True,
                        )


            # Add Space between cards and table
            st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### ⏱ Full Coverage Timeline")


            timeline_rows = []
            for rank, (ch, a) in enumerate(podium_list, start=1):
                ts = parse_ts(a.get("published_at", ""))
                delay_seconds = (ts - first_ts).total_seconds() if ts and first_ts else 0
                delay_str = format_time_gap(delay_seconds)

                timeline_rows.append({
                    "Rank": rank,
                    "Competitor": ch,
                    "Published At": ts.strftime("%Y-%m-%d %H:%M") if ts else "N/A",
                    "Time Gap": delay_str,
                    "Stories": channel_story_count.get(ch, 0),
                    "Title": a.get("title", ""),
                    "URL": a.get("url", ""),

                })

            timeline_df = pd.DataFrame(timeline_rows)
            render_frontend_table(
                timeline_df,
                "coverage_timeline_table",
                filename="coverage_timeline.csv",
                column_config={
                    "URL": st.column_config.LinkColumn("Link", display_text="Open"),
                },
                hide_controls=True
            )

            st.markdown("---")

            st.markdown("### 📺 Chronological Feed")

            feed_data = []
            for a in matched:
                ts = parse_ts(a.get("published_at", ""))
                delay_seconds = (ts - first_ts).total_seconds() if ts and first_ts else 0
                delay_label = format_time_gap(delay_seconds)

                feed_data.append({
                    "Time Gap": delay_label,
                    "Competitor": a.get("source", ""),
                    "Published At": ts.strftime("%Y-%m-%d %H:%M") if ts else "",
                    "Title": a.get("title", ""),
                    "URL": a.get("url", ""),
                    "Keywords": a.get("keywords", ""),
                })

            feed_df = pd.DataFrame(feed_data)
            render_frontend_table(
                feed_df,
                "chronological_feed_table",
                filename="chronological_feed.csv",
                column_config={
                    "URL": st.column_config.LinkColumn("Link", display_text="Open"),
                },
                hide_controls=True
            )


elif page == PAGE_DUPLICATES:
    st.markdown('<div class="section-title">🔁 Duplicate Content</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">All duplicate content across competitors — who published first and the time gap</div>', unsafe_allow_html=True)

    import datetime as dt
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        today = dt.date.today()
        local_date_range = st.date_input(
            "Date Range", 
            value=(today, today), 
            max_value=today,
            key="dup_date"
        )
        if isinstance(local_date_range, dt.date) and not isinstance(local_date_range, tuple):
            local_date_range = (local_date_range, local_date_range)
        elif isinstance(local_date_range, (list, tuple)) and len(local_date_range) == 1:
            local_date_range = (local_date_range[0], local_date_range[0])

    with filter_col2:
        all_sources = ["All"] + list(COMPETITORS.keys())
        local_source = st.selectbox("Source", all_sources, key="dup_source")
    
    with filter_col3:
        min_dup_score = st.number_input("Min Duplicate Score (%)", min_value=30, max_value=100, value=None, placeholder="Enter %", key="dup_min_score")

    if min_dup_score is None:
        st.info("Enter Min Duplicate Score (%) (30-100) and press Enter to see results.")
        st.stop()

    st.markdown("---")

    similar = analysis.get("similar_articles", []) if analysis else []

    cov_start, cov_end = local_date_range if (local_date_range and len(local_date_range) == 2) else (None, None)

    if local_source != "All":
        source_pairs = [
            p for p in similar
            if p["article_1"].get("source") == local_source or p["article_2"].get("source") == local_source
        ]
    else:
        source_pairs = similar

    filtered_pairs = []
    for pair in source_pairs:
        a1 = pair["article_1"]
        a2 = pair["article_2"]
        ts1 = parse_ts(a1.get("published_at", ""))
        ts2 = parse_ts(a2.get("published_at", ""))
        
        dup_score = pair.get("similarity_score", 0) * 100
        if min_dup_score is not None and dup_score < min_dup_score:
            continue

        if cov_start and cov_end and ts1 and ts2:
            date1 = ts1.date()
            date2 = ts2.date()
            if not ((cov_start <= date1 <= cov_end) or (cov_start <= date2 <= cov_end)):
                continue

        filtered_pairs.append(pair)

    filtered_pairs.sort(key=lambda p: p.get("similarity_score", 0), reverse=True)

    topic_groups = {}
    for pair in filtered_pairs:
        a1 = pair["article_1"]
        a2 = pair["article_2"]

        ts1 = parse_ts(a1.get("published_at", ""))
        ts2 = parse_ts(a2.get("published_at", ""))

        key1 = a1.get("title", "").strip()
        key2 = a2.get("title", "").strip()
        
        topic_key = min(key1[:100], key2[:100]) 

        if topic_key not in topic_groups:
            topic_groups[topic_key] = {"items": [], "full_titles": []}

        topic_groups[topic_key]["full_titles"].extend([key1, key2])

        if ts1 and ts2:
            time_gap = abs((ts2 - ts1).total_seconds())
        else:
            time_gap = 0

        topic_groups[topic_key]["items"].append({
            "article": a1,
            "ts": ts1,
            "time_gap": time_gap,
            "similarity": pair["similarity_score"],
        })
        topic_groups[topic_key]["items"].append({
            "article": a2,
            "ts": ts2,
            "time_gap": time_gap,
            "similarity": pair["similarity_score"],
        })

    grouped_results = []
    for t_key, group_data in topic_groups.items():
        items = group_data["items"]
        best_topic = max(group_data["full_titles"], key=len) if group_data["full_titles"] else t_key
        
        unique_articles = {}
        for item in items:
            art = item["article"]
            source = art.get("source", "")
            if source not in unique_articles:
                unique_articles[source] = item

        sorted_articles = sorted(
            [(source, data) for source, data in unique_articles.items() if data["ts"]],
            key=lambda x: x[1]["ts"]
        )


        if len(sorted_articles) > 1:


            first_ts = sorted_articles[0][1]["ts"]
            story_score = max(d["similarity"] for _, d in sorted_articles)
            grouped_results.append({
                "topic": best_topic,
                "publishers": sorted_articles,
                "first_ts": first_ts,
                "count": len(sorted_articles),
                "story_score": story_score,
            })


    grouped_results.sort(key=lambda x: x["story_score"], reverse=True)

    if not grouped_results:
        st.info("No duplicate content found in the current filters.")
    else:
        st.markdown("---")
        st.markdown("### Ranked Duplicates by Story")
        
        total_groups = len(grouped_results)
        page_size = 20
        total_pages = max(1, (total_groups + page_size - 1) // page_size)
        
        col_nav1, col_nav2 = st.columns([1, 2])
        with col_nav1:
            current_page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, key="dup_page")
        with col_nav2:
            st.markdown(f"<div style='text-align:center; padding-top:8px; color:var(--text-dim);'>Page {current_page} of {total_pages} | {total_groups} stories</div>", unsafe_allow_html=True)
        
        start_idx = (current_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_groups)
        page_groups = grouped_results[start_idx:end_idx]

        medal_colors = ["#FFD700", "#C0C0C0", "#CD7F32", "#2d2d3d", "#3d3d4d", "#4d4d5d", "#5d5d6d"]
        medal_icons = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]

        for g_idx, group in enumerate(page_groups, start=start_idx + 1):
            all_sims = [data["similarity"] for _, data in group["publishers"]]
            max_sim = max(all_sims) if all_sims else 0

            st.markdown(
                f"""
                <div class="stat-card" style="text-align: left; padding: 18px; margin-bottom: 20px;">
                    <div style="display: flex; align-items:center; justify-content: space-between; flex-wrap: nowrap; gap: 12px;">
                        <div style="display: flex; align-items: center; gap: 20px; flex: 1; min-width: 0;">
                            <span style="background: linear-gradient(135deg, var(--card-border), var(--primary)); color: white; font-weight: 800; font-size: 1.1rem; padding: 8px 16px; border-radius: 12px; min-width: 50px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.3); flex-shrink: 0;">
                                #{g_idx}
                            </span>
                            <div style="flex: 1; min-width: 0;">
                                <div style="font-size: 1.1rem; font-weight: 700; color: var(--text-main); margin-bottom: 2px; white-space: normal; overflow: visible;">{group['topic']}</div>
                            </div>
                        </div>
                        <div style="background: rgba(255, 75, 75, 0.1); border: 1px solid rgba(255, 75, 75, 0.3); padding: 6px 14px; border-radius: 30px; flex-shrink: 0;">
                            <span style="color: var(--primary); font-weight: 800; font-size: 0.8rem; letter-spacing: 0.5px;">
                                ANALYSIS SCORE: {max_sim:.1%}
                            </span>
                        </div>
                    </div>
                </div>

                """,
                unsafe_allow_html=True,
            )


            cols_per_row = min(group["count"], 7)
            row_cols = st.columns(cols_per_row)

            for p_idx, (source, data) in enumerate(group["publishers"]):
                if p_idx >= cols_per_row:
                    break
                ts = data["ts"]
                delay_seconds = (ts - group["first_ts"]).total_seconds() if ts and group["first_ts"] else 0

                medal_color = medal_colors[p_idx] if p_idx < len(medal_colors) else "#2d2d3d"
                medal_icon = medal_icons[p_idx] if p_idx < len(medal_icons) else f"{p_idx+1}️⃣"

                with row_cols[p_idx]:
                    st.markdown(
                        f"""<div class="stat-card" style="border-color:{medal_color}; border-width:2px; padding:16px; height:100%;">
                        <div class="stat-value" style="font-size:1.8rem;">{medal_icon}</div>
                        <div class="stat-label" style="color:var(--primary); font-size:0.8rem; font-weight:800; margin-top:8px;">{source}</div>
                        <div style="font-size:0.75rem; color:var(--text-dim); margin-top:4px;">{ts.strftime('%H:%M, %d %b') if ts else 'N/A'}</div>
                        <div style="font-size:0.85rem; font-weight:700; color:var(--text-main); margin-top:4px;">{format_time_gap(delay_seconds)}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

            st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)

            publishers_data = []
            for rank, (source, data) in enumerate(group["publishers"], start=1):

                art = data["article"]
                ts = data["ts"]
                delay_seconds = (ts - group["first_ts"]).total_seconds() if ts and group["first_ts"] else 0
                publishers_data.append({
                    "Rank": rank,
                    "Publisher": source,
                    "Published At": ts.strftime("%Y-%m-%d %H:%M") if ts else "N/A",
                    "Time Gap": format_time_gap(delay_seconds),
                    "Duplicate Score": f"{data['similarity']:.1%}",
                    "Title": art.get("title", ""),
                    "URL": art.get("url", ""),

                })

            publisher_df = pd.DataFrame(publishers_data)
            render_frontend_table(
                publisher_df,
                f"duplicate_story_{g_idx}_table",
                filename=f"duplicate_story_{g_idx:03}.csv",
                column_config={
                    "URL": st.column_config.LinkColumn("Link", display_text="Open"),
                },
                hide_controls=True,
            )

            st.markdown("---")

        st.markdown("### 📊 Summary Table")

        all_export_data = []
        for g_idx, group in enumerate(grouped_results):
            story_no = start_idx + 1 + g_idx
            dup_sr_no = f"DUP{story_no:03d}"
            for rank, (source, data) in enumerate(group["publishers"], start=1):
                art = data["article"]
                ts = data["ts"]
                delay_seconds = (ts - group["first_ts"]).total_seconds() if ts and group["first_ts"] else 0
                all_export_data.append({
                    "Duplicate_Sr_no.": dup_sr_no,
                    "Rank": rank,
                    "Publisher": source,
                    "Published At": ts.strftime("%Y-%m-%d %H:%M") if ts else "N/A",
                    "Time Gap": format_time_gap(delay_seconds),
                    "Duplicate %": round(data["similarity"] * 100, 1),
                    "Title": art.get("title", ""),
                    "URL": art.get("url", ""),
                })

        export_df = pd.DataFrame(all_export_data)
        if not export_df.empty:
            export_df = export_df.sort_values("Duplicate %", ascending=False).reset_index(drop=True)

        render_frontend_table(
            export_df,
            "duplicate_summary_table",
            filename="duplicate_summary.csv",
            column_config={
                "Duplicate %": st.column_config.NumberColumn("Duplicate %", format="%.1f%%"),
                "URL": st.column_config.LinkColumn("Link", display_text="Open"),
            },
            hide_controls=True,
        )

elif page == PAGE_DATE_WISE:
    st.markdown('<div class="section-title">📊 Raw Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Chronological distribution of content volume across all monitored channels.</div>', unsafe_allow_html=True)

    import datetime as dt
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        today = dt.date.today()
        local_date_range = st.date_input("Date Range", value=(today, today), key="date_wise_date")
        # Normalize single-date return when start == end
        if isinstance(local_date_range, dt.date) and not isinstance(local_date_range, tuple):
            local_date_range = (local_date_range, local_date_range)
        elif isinstance(local_date_range, (list, tuple)) and len(local_date_range) == 1:
            local_date_range = (local_date_range[0], local_date_range[0])
    with filter_col2:
        all_sources = ["All"] + list(COMPETITORS.keys())
        local_source = st.selectbox("Source", all_sources, key="date_wise_source")



    # ---- Filtered Articles for Pivot Table ----

    filtered_articles = []
    for pa in parsed_articles:
        a = pa["article"]
        ts = pa["ts"]
        if not ts:
            continue
            
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        
        if local_source != "All" and a.get("source") != local_source:
            continue
        
        article_date = ts.date()
        
        if local_date_range and len(local_date_range) == 2:
            cov_start, cov_end = local_date_range
            if not (cov_start <= article_date <= cov_end):
                continue



        
        filtered_articles.append((ts, a))

    if not filtered_articles:
        st.info("No articles found in the selected date range.")
    else:
        date_source_counts = {}
        for ts, a in filtered_articles:
            date_key = ts.strftime("%Y-%m-%d")
            source = a.get("source", "Unknown")
            if date_key not in date_source_counts:
                date_source_counts[date_key] = {}
            date_source_counts[date_key][source] = date_source_counts[date_key].get(source, 0) + 1

        all_dates = sorted(date_source_counts.keys(), reverse=True)
        all_sources_in_data = sorted(set(s for d in date_source_counts for s in date_source_counts[d].keys()))

        pivot_rows = []
        for source in all_sources_in_data:
            row = {"Channel": source}
            row_total = 0
            for date_key in all_dates:
                count = date_source_counts[date_key].get(source, 0)
                row[date_key] = count
                row_total += count
            row["Total"] = row_total
            pivot_rows.append(row)

        total_row = {"Channel": "**Day Total**"}
        grand_total = 0
        for date_key in all_dates:
            day_total = sum(date_source_counts[date_key].get(source, 0) for source in all_sources_in_data)
            total_row[date_key] = day_total
            grand_total += day_total
        total_row["Total"] = grand_total
        pivot_rows.append(total_row)

        pivot_df = pd.DataFrame(pivot_rows)
        pivot_df = pivot_df.set_index("Channel")
        pivot_df.index.name = None

        def styler_func(s, pivot_df=pivot_df):
            is_total_row = pivot_df.index[pivot_df.index.get_indexer([s.index[0]])[0]] == "**Day Total**"
            if is_total_row:
                return ['min-width: 130px; text-align: center; font-weight: bold; background: rgba(255,75,75,0.1); font-size: 1.2rem;' for _ in s]
            return ['min-width: 130px; text-align: center; font-size: 1.2rem;' for _ in s]


        styler = pivot_df.style.apply(styler_func).set_properties(**{
            'text-align': 'center',
            'border': '1px solid rgba(255,255,255,0.05)',
        }).set_table_styles([
            {'selector': 'th', 'props': [('text-align', 'center'), ('padding', '8px'), ('background', 'rgba(10,10,15,0.95)')]},
            {'selector': 'td', 'props': [('padding', '8px')]},
        ])

        pivot_height = (len(pivot_df) + 1) * 45 + 50

        st.dataframe(
            styler,
            use_container_width=True,
            height=pivot_height,
        )


elif page == PAGE_LATEST:
    st.markdown('<div class="section-title">🏠 Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Real-time feed of the most recently published content across all platforms.</div>', unsafe_allow_html=True)
    
    local_date_range, local_source, lookback_min = get_filters("latest_tab", include_hours=True)
    
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    min_threshold = now - timedelta(minutes=lookback_min)
    
    latest_articles = []
    start_date, end_date = local_date_range if (local_date_range and len(local_date_range) == 2) else (None, None)

    for pa in parsed_articles:
        a = pa["article"]
        ts = pa["ts"]
        
        if local_source != "All" and a.get("source") != local_source:
            continue
            
        if not ts:
            continue
            
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        
        if start_date and end_date:
            article_date = ts.date()
            if not (start_date <= article_date <= end_date):
                continue
    
        if not start_date or start_date == now.date():
             if ts < min_threshold:
                 continue
        
        latest_articles.append({
            "Published": ts.strftime("%Y-%m-%d"),
            "Time": ts.strftime("%I:%M %p"),
            "Channel": a.get("source"),
            "Title": a.get("title"),
            "URL": a.get("url"),
        })
            
    if not latest_articles:
        st.info("No articles found matching the current criteria.")
    else:
        latest_df = pd.DataFrame(latest_articles)
        latest_df = latest_df.sort_values(["Published", "Time"], ascending=False)
        
        st.success(f"Found **{len(latest_articles)}** articles.")
        
        sources = sorted(latest_df["Channel"].unique())
        
        if local_source != "All":
            st.markdown(f"### {local_source}")
            render_frontend_table(
                latest_df,
                f"latest_{local_source}_single_table",
                filename=f"latest_{local_source}.csv",
                column_config={
                    "URL": st.column_config.LinkColumn("Link", display_text="Open"),
                    "Title": st.column_config.TextColumn("Title", width="large"),
                },
                hide_controls=True
            )
        elif sources:
            all_count = len(latest_df)
            tab_names = [f"All Sources ({all_count})"]
            for s in sources:
                count = len(latest_df[latest_df["Channel"] == s])
                tab_names.append(f"{s} ({count})")
            
            tabs = st.tabs(tab_names)
            
            with tabs[0]:
                render_frontend_table(
                    latest_df,
                    "latest_all_combined_table",
                    filename="latest_all_sources.csv",
                    column_config={
                        "URL": st.column_config.LinkColumn("Link", display_text="Open"),
                        "Title": st.column_config.TextColumn("Title", width="large"),
                    },
                    hide_controls=True
                )
            
            for i, source in enumerate(sources):
                with tabs[i+1]:
                    src_df = latest_df[latest_df["Channel"] == source]
                    render_frontend_table(
                        src_df,
                        f"latest_{source}_tab_table",
                        filename=f"latest_{source}.csv",
                        column_config={
                            "URL": st.column_config.LinkColumn("Link", display_text="Open"),
                            "Title": st.column_config.TextColumn("Title", width="large"),
                        },
                        hide_controls=True
                    )
        else:
            st.warning("No articles categorized by source found.")
