"""Local Streamlit dashboard for Reddit ticker sentiment/attention.

Read-only view over the local SQLite DB populated by run_pipeline.py.
This surfaces attention and tone; it does not predict price moves and
does not place or suggest trades.

Run with: streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from storage.db import get_connection, get_db_path, init_db  # noqa: E402

st.set_page_config(page_title="Reddit Ticker Sentiment", layout="wide")

st.title("Reddit Ticker Sentiment & Attention Tracker")
st.caption(
    "Read-only sentiment/attention monitor based on Reddit discussion. "
    "This is a decision-support signal only — not a price prediction, "
    "not investment advice, not connected to any trading account."
)

if not get_db_path().exists():
    init_db()
    st.warning(
        "No data yet. Run `python run_pipeline.py` first to pull and score "
        "Reddit activity."
    )
    st.stop()

with get_connection() as conn:
    snapshots = pd.read_sql_query(
        "SELECT * FROM ticker_snapshots ORDER BY run_at DESC", conn
    )
    mentions = pd.read_sql_query(
        "SELECT * FROM mentions ORDER BY created_utc DESC LIMIT 500", conn
    )

if snapshots.empty:
    st.warning(
        "No snapshots recorded yet. Run `python run_pipeline.py` to populate data."
    )
    st.stop()

snapshots["run_at"] = pd.to_datetime(snapshots["run_at"])
latest_run = snapshots["run_at"].max()
latest = snapshots[snapshots["run_at"] == latest_run]

st.subheader(f"Latest snapshot — {latest_run.strftime('%Y-%m-%d %H:%M UTC')}")

col_count = min(len(latest), 5) or 1
cols = st.columns(col_count)
latest_sorted = latest.sort_values("mention_count", ascending=False)
for i, (_, row) in enumerate(latest_sorted.head(col_count).iterrows()):
    with cols[i % col_count]:
        st.metric(
            label=row["ticker"],
            value=f"{row['mention_count']} mentions",
            delta=f"{row['avg_signed_score']:.2f} tone",
        )

st.subheader("All tickers — latest snapshot")
st.dataframe(
    latest_sorted[
        [
            "ticker",
            "mention_count",
            "avg_signed_score",
            "positive_count",
            "negative_count",
            "neutral_count",
        ]
    ].reset_index(drop=True),
    use_container_width=True,
)

st.subheader("Attention & tone over time")
ticker_options = sorted(snapshots["ticker"].unique())
selected = st.multiselect(
    "Tickers to chart", ticker_options, default=ticker_options[: min(5, len(ticker_options))]
)
if selected:
    chart_data = snapshots[snapshots["ticker"].isin(selected)]

    mention_pivot = chart_data.pivot_table(
        index="run_at", columns="ticker", values="mention_count", aggfunc="sum"
    )
    st.caption("Mention count per run")
    st.line_chart(mention_pivot)

    sentiment_pivot = chart_data.pivot_table(
        index="run_at", columns="ticker", values="avg_signed_score", aggfunc="mean"
    )
    st.caption("Average signed sentiment per run (-1 = negative, +1 = positive)")
    st.line_chart(sentiment_pivot)

st.subheader("Recent individual mentions")
ticker_filter = st.selectbox("Filter by ticker", ["All"] + ticker_options)
display_mentions = mentions if ticker_filter == "All" else mentions[mentions["ticker"] == ticker_filter]
st.dataframe(
    display_mentions[
        ["created_utc", "ticker", "subreddit", "kind", "sentiment_label", "signed_score", "permalink"]
    ].reset_index(drop=True),
    use_container_width=True,
)
