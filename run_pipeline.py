#!/usr/bin/env python3
"""One-shot pipeline: pull recent Reddit activity, extract ticker mentions,
score sentiment with FinBERT, and store results in SQLite.

This is a read-only attention/sentiment tracker. It makes no price
predictions and takes no trading actions.

Usage:
    python run_pipeline.py

Schedule this with cron / Task Scheduler to run periodically.
"""
import sys
from collections import defaultdict
from datetime import datetime, timezone

from config.settings import ConfigError, load_watchlist
from ingest.reddit_client import fetch_recent_items, get_reddit_instance
from ingest.ticker_matcher import extract_mentions
from sentiment.finbert_scorer import score_text
from storage.db import get_connection, init_db, insert_mention, insert_snapshot


def main() -> int:
    try:
        watchlist = load_watchlist()
    except FileNotFoundError:
        print("config/watchlist.yaml not found.", file=sys.stderr)
        return 1

    tickers = watchlist["tickers"]
    ambiguous = {t.upper() for t in watchlist.get("ambiguous_tickers", [])}
    subreddits = watchlist["subreddits"]
    post_limit = watchlist.get("post_limit", 50)
    comments_per_post = watchlist.get("comments_per_post", 20)

    try:
        reddit = get_reddit_instance()
    except ConfigError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    print(f"Fetching from subreddits: {subreddits} (post_limit={post_limit})")
    items = fetch_recent_items(
        reddit, subreddits, post_limit=post_limit, comments_per_post=comments_per_post
    )
    print(f"Fetched {len(items)} items (posts + comments).")

    init_db()
    run_at = datetime.now(timezone.utc)

    # ticker -> list of signed sentiment scores collected this run
    ticker_scores: dict[str, list[float]] = defaultdict(list)
    ticker_label_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {"positive": 0, "negative": 0, "neutral": 0}
    )

    with get_connection() as conn:
        for item in items:
            text = f"{item.title or ''} {item.body or ''}".strip()
            mentioned = extract_mentions(text, tickers, ambiguous)
            if not mentioned:
                continue

            result = score_text(text)

            for ticker in mentioned:
                insert_mention(
                    conn,
                    reddit_item_id=item.item_id,
                    kind=item.kind,
                    subreddit=item.subreddit,
                    ticker=ticker,
                    sentiment_label=result.label,
                    sentiment_score=result.score,
                    signed_score=result.signed_score,
                    item_score=item.score,
                    permalink=item.permalink,
                    created_utc=item.created_utc,
                )
                ticker_scores[ticker].append(result.signed_score)
                ticker_label_counts[ticker][result.label] += 1

        for ticker, scores in ticker_scores.items():
            avg_signed = sum(scores) / len(scores) if scores else 0.0
            counts = ticker_label_counts[ticker]
            insert_snapshot(
                conn,
                ticker=ticker,
                run_at=run_at,
                mention_count=len(scores),
                avg_signed_score=avg_signed,
                positive_count=counts["positive"],
                negative_count=counts["negative"],
                neutral_count=counts["neutral"],
            )
            print(
                f"  {ticker}: {len(scores)} mentions, "
                f"avg_signed_score={avg_signed:.3f}"
            )

    print("Pipeline run complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
