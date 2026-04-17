"""
Breaking News Finder - Streamlit Dashboard
Zee Gujarati Competitor Analysis Tool
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timezone
from io import BytesIO
import os
import sys
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import COMPETITORS
from sitemap_parser import fetch_all_competitors
from nlp_engine import NewsAnalyzer, run_full_analysis
from data_store import save_articles, load_articles, save_analysis, load_analysis, get_data_freshness

st.set_page_config(
    page_title="Breaking News Finder | Zee Gujarati",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGE_COVERAGE = "🏁 Coverage Race"
PAGE_DUPLICATES = "🔁 Duplicate Content"

st.set_page_config(
    page_title="Breaking News Finder | Zee Gujarati",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    :root {
        --accent-red: #FF3D71;
        --accent-pink: #C850C0;
        --accent-purple: #4158D0;
        --accent-blue: #2BD2FF;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #050508 0%, #0a0a0f 100%);
        border-right: 1px solid rgba(255,255,255,0.03);
    }

    [data-testid="stSidebar"] section::-webkit-scrollbar {
        display: none;
    }

    [data-testid="stSidebar"] .stMarkdown h1 {
        background: linear-gradient(135deg, #FF6B6B, #FF3D71);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 61, 113, 0.4); }
        70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(255, 61, 113, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 61, 113, 0); }
    }

    .stat-card {
        background: linear-gradient(135deg, rgba(10,10,15,0.95), rgba(15,15,22,0.95));
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        backdrop-filter: blur(10px);
        animation: fadeInUp 0.6s ease-out forwards;
    }

    .stat-card:hover {
        border-color: rgba(255,61,113,0.3);
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }

    .stat-value {
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -1px;
    }

    .stat-label {
        font-size: 0.72rem;
        color: #9898b0;
    }

    .section-title {
        font-size: 1.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF6B6B, #FF3D71);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }

    .section-subtitle {
        color: #9898b0;
        font-size: 0.9rem;
        margin-bottom: 24px;
    }

    .gradient-text-red { background: linear-gradient(135deg, #FF6B6B, #FF3D71); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .gradient-text-purple { background: linear-gradient(135deg, #4158D0, #C850C0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .gradient-text-green { background: linear-gradient(135deg, #00C9FF, #92FE9D); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .gradient-text-warm { background: linear-gradient(135deg, #FA8BFF, #2BD2FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

    .stButton > button {
        border-radius: 12px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }

    .stDataFrame { border-radius: 10px; overflow: hidden; }

    div[data-testid="stExpander"] {
        background: rgba(10, 10, 15, 0.98);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 12px;
    }

    .stApp::before {
        content: '';
        position: fixed;
        top: -10%;
        right: -5%;
        width: 500px;
        height: 500px;
        background: #FF3D71;
        filter: blur(150px);
        opacity: 0.05;
        pointer-events: none;
    }

    .tag-pill {
        display: inline-block;
        font-size: 0.68rem;
        padding: 2px 8px;
        background: rgba(255, 61, 113, 0.1);
        color: #FF3D71;
        border-radius: 4px;
        margin: 2px;
        font-weight: 600;
    }
</style>
""",
    unsafe_allow_html=True,
)


def format_number(num):
    if num is None:
        return "0"
    if num >= 10_000_000:
        return f"{num / 10_000_000:.1f} Cr"
    if num >= 100_000:
        return f"{num / 100_000:.1f} L"
    if num >= 1000:
        return f"{num / 1000:.1f}K"
    return f"{num:,}"


def render_frontend_table(df, key, column_config=None, filename=None, hide_controls=False):
    filename = filename or f"{key}.csv"
    expand_key = f"{key}_expand"

    if not hide_controls:
        _, col_download, col_expand = st.columns([6, 1, 1])

        with col_download:
            st.download_button(
                label="⬇️",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name=filename,
                mime="text/csv",
                key=f"{key}_download",
            )

        with col_expand:
            if st.button("🔍", key=f"{key}_expand_button"):
                st.session_state[expand_key] = not st.session_state.get(expand_key, False)

    is_expanded = st.session_state.get(expand_key, False)

    if is_expanded:
        st.write("### Fullscreen View")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        key=key,
        height=600 if is_expanded else "content",
    )




def get_filters(key_prefix):
    import datetime
    from datetime import timedelta
    
    with st.expander("🔍 Filters & Tools", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            today = datetime.date.today()
            date_range = st.date_input(
                "Date Range",
                value=(today, today),
                help="Filter by date",
                key=f"{key_prefix}_date"
            )
            
        with col2:
            all_sources = ["All"] + list(COMPETITORS.keys())
            source = st.selectbox("Source", all_sources, key=f"{key_prefix}_source")
            
        with col3:
            st.write("")
            
    return date_range, source


with st.sidebar:
    st.markdown("# 📰 News Finder")
    st.caption("Competitor Analysis")
    
    freshness = get_data_freshness()
    if freshness:
        try:
            dt_utc = datetime.fromisoformat(freshness.replace("Z", "+00:00"))
            now_utc = datetime.now(timezone.utc)
            diff = now_utc - dt_utc
            seconds = diff.total_seconds()
            if seconds < 60:
                time_str = "Just now"
            elif seconds < 3600:
                time_str = f"{int(seconds // 60)} mins ago"
            elif seconds < 86400:
                time_str = f"{int(seconds // 3600)} hrs ago"
            else:
                time_str = f"{int(seconds // 86400)} days ago"
            st.markdown(f"""
                <div style="font-size: 0.75rem; color: #2BD2FF; background: rgba(43, 210, 255, 0.1); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(43, 210, 255, 0.2); font-weight: 600;">
                    💾 Updated {time_str}
                </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.info(f"💾 Refresh: {freshness[:16]}")
    else:
        st.caption("📅 No data cached yet")

    st.divider()

    page = st.radio(
        "Navigate",
        [PAGE_COVERAGE, PAGE_DUPLICATES],
        label_visibility="collapsed",
    )

    st.divider()

    hours = st.slider("Lookback window (hours)", 1, 72, 48, step=1)

    st.divider()

    fetch_btn = st.button("🚀 Fetch & Analyze", use_container_width=True, type="primary")
    load_btn = st.button("📂 Load Cached Data", use_container_width=True)

if "articles" not in st.session_state:
    st.session_state.articles = []
if "analysis" not in st.session_state:
    st.session_state.analysis = None

if fetch_btn:
    with st.status("🔄 Fetching sitemaps from all competitors...", expanded=True) as status:
        st.write("Connecting to 6 competitor sitemaps...")
        articles = fetch_all_competitors(hours=hours)
        st.write(f"✅ Fetched **{len(articles)}** articles")

        if articles:
            save_articles(articles)
            st.write("💾 Saved to JSON")

            st.write("🧠 Running NLP analysis...")
            analysis = run_full_analysis(articles)
            save_analysis(analysis)
            st.write("✅ Analysis complete!")

            st.session_state.articles = articles
            st.session_state.analysis = analysis
            status.update(label=f"✅ Done — {len(articles)} articles analyzed", state="complete")
        else:
            status.update(label="⚠️ No articles found", state="error")

if load_btn:
    articles = load_articles()
    analysis = load_analysis()
    if articles:
        st.session_state.articles = articles
        st.session_state.analysis = analysis
        st.success(f"Loaded {len(articles)} cached articles")
    else:
        st.warning("No cached data found. Click 'Fetch & Analyze' first.")

articles = st.session_state.articles
analysis = st.session_state.analysis

if not articles:
    st.markdown(
        """
        <div style="text-align:center; padding:80px 20px;">
            <h1 style="font-size:3rem; margin-bottom:16px;">📰</h1>
            <h2 style="color: #FF3D71;">No Data Found</h2>
            <p style="color:#9898b0; margin-top:8px; font-size: 1.2rem;">
                It looks like there's no data available yet. <br>
                <strong>Kindly fetch fresh data first</strong> using the button in the sidebar.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

df = pd.DataFrame(articles)
summary = analysis.get("summary", {}) if analysis else {}
color_map = {name: cfg["color"] for name, cfg in COMPETITORS.items()}

if page == PAGE_COVERAGE:
    st.markdown('<div class="section-title">🏁 Coverage Race</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Identify which competitor broke a story first — and by how many minutes</div>', unsafe_allow_html=True)

    local_date_range, local_source = get_filters("coverage")

    st.markdown("---")

    topic_query = st.text_input(
        "🔎 Enter topic keywords",
        placeholder="Type breaking news keyword...",
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
        for a in articles:
            pub_str = a.get("published_at", "")
            if not pub_str:
                continue
            try:
                pub_date = pd.to_datetime(pub_str).date()
            except Exception:
                continue
            if cov_start and cov_end and not (cov_start <= pub_date <= cov_end):
                continue

            if local_source != "All" and a.get("source") != local_source:
                continue

            title_text = a.get("title", "").lower()
            keywords_text = a.get("keywords", "").lower()
            source_text = a.get("source", "").lower()
            url_text = a.get("url", "").lower()
            combined = title_text + " " + keywords_text + " " + source_text + " " + url_text
            
            if all(tok in combined for tok in query_tokens if len(tok) > 2):
                matched.append(a)

        if not matched:
            st.warning(f'No articles found for **"{topic_query}"** in the selected date range.')
        else:
            matched.sort(key=lambda x: x.get("published_at", ""))

            def parse_ts(pub_str):
                try:
                    return pd.to_datetime(pub_str)
                except Exception:
                    return None

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
                row_cols = st.columns(cols_per_row)
                
                for idx, (ch, a) in enumerate(row_channels):
                    total_idx = i + idx
                    ts = parse_ts(a.get("published_at", ""))
                    delay_mins = round((ts - first_ts).total_seconds() / 60) if ts and first_ts else 0
                    
                    medal_color = medal_colors[total_idx] if total_idx < 3 else "#2d2d3d"
                    medal_icon = medal_icons[total_idx] if total_idx < 3 else "📺"
                    
                    with row_cols[idx]:
                        story_count = channel_story_count.get(ch, 0)
                        st.markdown(
                            f"""<div class="stat-card" style="border-color:{medal_color};border-width:2px; height:100%;">
                            <div class="stat-value" style="font-size:2.2rem;">{medal_icon}</div>
                            <div class="stat-value gradient-text-warm" style="font-size:1rem;margin-top:6px;">{ch}</div>
                            <div class="stat-label" style="margin-top:6px;">{ts.strftime('%H:%M, %d %b') if ts else 'N/A'}</div>
                            <div class="stat-label">{"🚀 First!" if delay_mins == 0 else f"+{delay_mins} min late"}</div>
                            <div class="stat-label">📰 {story_count} {'story' if story_count == 1 else 'stories'}</div>
                            </div>""",
                            unsafe_allow_html=True,
                        )

            st.markdown("---")

            st.markdown("### ⏱ Full Coverage Timeline")

            timeline_rows = []
            for rank, (ch, a) in enumerate(podium_list, start=1):
                ts = parse_ts(a.get("published_at", ""))
                delay_mins = round((ts - first_ts).total_seconds() / 60) if ts and first_ts else 0
                delay_hrs = delay_mins // 60
                delay_rem = delay_mins % 60

                if delay_mins == 0:
                    delay_str = "🚀 First!"
                elif delay_hrs > 0:
                    delay_str = f"+{delay_hrs}h {delay_rem}m"
                else:
                    delay_str = f"+{delay_mins}m"

                timeline_rows.append({
                    "Rank": rank,
                    "Competitor": ch,
                    "Published At": ts.strftime("%Y-%m-%d %H:%M") if ts else "N/A",
                    "Time Gap": delay_str,
                    "Stories": channel_story_count.get(ch, 0),
                    "Title": a.get("title", "")[:80],
                })

            timeline_df = pd.DataFrame(timeline_rows)
            render_frontend_table(
                timeline_df,
                "coverage_timeline_table",
                filename="coverage_timeline.csv",
            )

            st.markdown("---")

            st.markdown("### 📺 Chronological Feed")

            feed_data = []
            for a in matched:
                ts = parse_ts(a.get("published_at", ""))
                delay_mins = round((ts - first_ts).total_seconds() / 60) if ts and first_ts else 0

                if delay_mins == 0:
                    delay_label = "🚀 FIRST"
                else:
                    hrs = delay_mins // 60
                    mins = delay_mins % 60
                    delay_label = f"+{hrs}h {mins}m" if hrs > 0 else f"+{mins}m"

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
                }
            )

elif page == PAGE_DUPLICATES:
    st.markdown('<div class="section-title">🔁 Duplicate Content</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">All duplicate content across competitors — who published first and the time gap</div>', unsafe_allow_html=True)

    import datetime as dt
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        today = dt.date.today()
        local_date_range = st.date_input("Date Range", value=(today, today), key="dup_date")
    with filter_col2:
        all_sources = ["All"] + list(COMPETITORS.keys())
        local_source = st.selectbox("Source", all_sources, key="dup_source")

    st.markdown("---")

    similar = analysis.get("similar_articles", []) if analysis else []

    def parse_ts(pub_str):
        try:
            ts = pd.to_datetime(pub_str)
            return None if pd.isna(ts) else ts
        except Exception:
            return None

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

        key1 = a1.get("title", "")[:50]
        key2 = a2.get("title", "")[:50]
        topic_key = min(key1, key2)

        if topic_key not in topic_groups:
            topic_groups[topic_key] = []

        if ts1 and ts2:
            if ts1 < ts2:
                time_gap = (ts2 - ts1).total_seconds() / 60
            else:
                time_gap = (ts1 - ts2).total_seconds() / 60
        else:
            time_gap = 0

        topic_groups[topic_key].append({
            "article": a1,
            "ts": ts1,
            "time_gap": time_gap,
            "similarity": pair["similarity_score"],
        })
        topic_groups[topic_key].append({
            "article": a2,
            "ts": ts2,
            "time_gap": time_gap,
            "similarity": pair["similarity_score"],
        })

    grouped_results = []
    for topic, items in topic_groups.items():
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
                "topic": topic,
                "publishers": sorted_articles,
                "first_ts": first_ts,
                "count": len(sorted_articles),
                "story_score": story_score,
            })

    grouped_results.sort(key=lambda x: x["story_score"], reverse=True)

    if not grouped_results:
        st.info("No duplicate content found in the current filters.")
    else:
        total_pairs = sum(len(g["publishers"]) - 1 for g in grouped_results)
        total_gaps = []
        for g in grouped_results:
            for i in range(1, len(g["publishers"])):
                if g["publishers"][i][1]["ts"] and g["publishers"][0][1]["ts"]:
                    gap = (g["publishers"][i][1]["ts"] - g["first_ts"]).total_seconds() / 60
                    total_gaps.append(gap)

        cols = st.columns(5)
        all_sims = []
        for g in grouped_results:
            for _, data in g["publishers"]:
                all_sims.append(data["similarity"])
        avg_score = round((sum(all_sims) / len(all_sims)) * 100, 1) if all_sims else 0
        max_score = round(max(all_sims) * 100, 1) if all_sims else 0

        metrics = [
            ("Duplicate Stories", len(grouped_results), "🔁"),
            ("Total Publishers", sum(g["count"] for g in grouped_results), "📰"),
            ("Avg Gap (min)", round(sum(total_gaps) / len(total_gaps), 1) if total_gaps else 0, "⏱️"),
            ("Fastest Follow (min)", min(total_gaps) if total_gaps else 0, "🚀"),
            ("Duplicate Score", f"{avg_score}%", "📊"),
        ]
        for col, (label, value, icon) in zip(cols, metrics):
            col.markdown(f"""
            <div class="stat-card">
                <div style="font-size:1.5rem">{icon}</div>
                <div class="stat-value gradient-text-warm">{value}</div>
                <div class="stat-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### Ranked Duplicates by Story")

        medal_colors = ["#FFD700", "#C0C0C0", "#CD7F32", "#2d2d3d", "#3d3d4d", "#4d4d5d", "#5d5d6d"]
        medal_icons = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣"]

        for g_idx, group in enumerate(grouped_results, start=1):
            all_sims = [data["similarity"] for _, data in group["publishers"]]
            max_sim = max(all_sims) if all_sims else 0
            avg_sim = sum(all_sims) / len(all_sims) if all_sims else 0

            score_color = "#FFD700" if max_sim >= 0.8 else "#FF6B6B" if max_sim >= 0.5 else "#2BD2FF"
            score_bg = f"background: rgba({int(max_sim*255)}, {int(100*max_sim)}, {int(150*(1-max_sim))}, 0.15);"

            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, rgba(10,10,15,0.98), rgba(15,15,22,0.98)); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <span style="background: linear-gradient(135deg, #FF3D71, #FF6B6B); color: white; font-weight: 800; font-size: 1.1rem; padding: 8px 14px; border-radius: 10px; min-width: 50px; text-align: center;">
                                #{g_idx}
                            </span>
                            <div>
                                <div style="font-size: 1.1rem; color: #9898b0; margin-bottom: 4px;">{group['topic']}</div>
                                <div style="font-size: 0.85rem; color: #5e5e78;">📰 {group['count']} competitors covered this story</div>
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 16px;">
                            <span class="tag-pill" style="background: {score_bg}; color: {score_color}; border: 1px solid {score_color}; font-size: 1rem; padding: 6px 14px; border-radius: 20px; font-weight: 700;">
                                📊 Duplicate Score: {max_sim:.1%}
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
                art = data["article"]
                ts = data["ts"]
                delay = (ts - group["first_ts"]).total_seconds() / 60 if ts and group["first_ts"] else 0

                medal_color = medal_colors[p_idx] if p_idx < len(medal_colors) else "#2d2d3d"
                medal_icon = medal_icons[p_idx] if p_idx < len(medal_icons) else f"{p_idx+1}️⃣"

                with row_cols[p_idx]:
                    st.markdown(
                        f"""<div class="stat-card" style="border-color:{medal_color};border-width:2px;padding:16px;">
                        <div class="stat-value" style="font-size:1.5rem;">{medal_icon}</div>
                        <div class="stat-value gradient-text-warm" style="font-size:0.9rem;margin-top:4px;">{source}</div>
                        <div class="stat-label" style="font-size:0.8rem;">{ts.strftime('%H:%M, %d %b') if ts else 'N/A'}</div>
                        <div class="stat-label" style="font-size:0.8rem;">{"🚀 First!" if delay == 0 else f"+{delay:.0f} min"}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

            publishers_data = []
            for rank, (source, data) in enumerate(group["publishers"], start=1):
                art = data["article"]
                ts = data["ts"]
                delay = (ts - group["first_ts"]).total_seconds() / 60 if ts and group["first_ts"] else 0
                publishers_data.append({
                    "Rank": rank,
                    "Publisher": source,
                    "Published At": ts.strftime("%Y-%m-%d %H:%M") if ts else "N/A",
                    "Time Gap": "🚀 First!" if delay == 0 else f"+{delay:.0f} min",
                    "Duplicate Score": f"{data['similarity']:.1%}",
                    "Similarity": f"{data['similarity']:.1%}",
                    "Title": art.get("title", "")[:60],
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
            story_no = 101 + g_idx
            dup_sr_no = f"DUP{str(story_no)}"
            for rank, (source, data) in enumerate(group["publishers"], start=1):
                art = data["article"]
                ts = data["ts"]
                delay = (ts - group["first_ts"]).total_seconds() / 60 if ts and group["first_ts"] else 0
                all_export_data.append({
                    "Duplicate_Sr_no.": dup_sr_no,
                    "Rank": rank,
                    "Publisher": source,
                    "Published At": ts.strftime("%Y-%m-%d %H:%M") if ts else "N/A",
                    "Time Gap (min)": "0" if delay == 0 else f"+{delay:.0f}",
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


if st.session_state.get("fetching_now", False):
    with st.status("Fetching latest data...", expanded=True) as status:
        st.write("Initializing Optimized Parallel Fetcher...")
        try:
            from fetch_data import fetch_all_channels
            videos = fetch_all_channels()
            st.write(f"Successfully fetched {len(videos)} videos!")
            st.cache_resource.clear()
            st.session_state.fetching_now = False
            status.update(label="Fetch Complete!", state="complete", expanded=False)
            st.rerun()
        except Exception as exc:
            st.session_state.fetching_now = False
            st.error(f"Could not fetch data: {exc}")
            status.update(label="Fetch Failed", state="error")
