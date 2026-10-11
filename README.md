# Reddit Sentiment Dashboard

A **read-only, local** sentiment/attention tracker for a watchlist of stock tickers,
based on Reddit discussion volume and tone. This is a decision-support dashboard,
**not** a predictive trading signal and **not** connected to any brokerage or
automated trading system.

## What this is

- Pulls recent posts/comments from a configurable list of subreddits (e.g.
  r/wallstreetbets, r/stocks, r/investing) via Reddit's official API (PRAW).
- Extracts ticker mentions (cashtags / watchlist matching) with false-positive
  filtering (e.g. "IT", "ON", "ALL" are common words as well as tickers).
- Scores sentiment per mention using FinBERT (finance-tuned sentiment model),
  run locally via `transformers`.
- Aggregates mention count, sentiment, and attention velocity per ticker per
  time window into a local SQLite database.
- Displays it all in a local Streamlit dashboard.

## What this deliberately is NOT

- Not a backtested trading strategy. There are no price-correlation or
  "predictive accuracy" claims anywhere in this codebase.
- Not connected to any brokerage, order execution, or automated trading.
- Not a mass-scraping tool. It respects Reddit's API rate limits and ToS.

## Project layout

```
Project/
  config/           # settings, watchlist, subreddit list, .env for credentials
  ingest/           # Reddit pull via PRAW
  sentiment/        # FinBERT scoring
  storage/          # SQLite schema + read/write helpers
  dashboard/        # Streamlit app
  data/             # local SQLite DB lives here (gitignored)
  run_pipeline.py   # one-shot: pull -> score -> store
```

## Setup

### 1. Reddit API credentials

You need a Reddit API app (free):

1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. Choose type **script**
4. Name it anything (e.g. `local-sentiment-tracker`), leave the "about url"
   blank, and set the "redirect uri" to `http://localhost:8080`
5. After creating, copy the **client ID** (string under the app name) and
   **client secret**.

Copy `config/.env.example` to `config/.env` and fill in:

```
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=local-sentiment-tracker by u/yourusername
```

Never commit `.env`. It's already in `.gitignore`.

### 2. Python environment

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on native Windows
pip install -r requirements.txt
```

First run will download the FinBERT model (~400MB) from Hugging Face.

### 3. Configure your watchlist

Edit `config/watchlist.yaml` to set tickers and subreddits to track.

### 4. Run the pipeline

```bash
python run_pipeline.py
```

This does one pull-score-store cycle. Schedule it with cron (or Windows Task
Scheduler) to run periodically, e.g. every 30-60 minutes.

### 5. View the dashboard

```bash
streamlit run dashboard/app.py
```

## Notes on data access

Reddit restricted free API access in 2023. This project uses the official
API via PRAW within standard rate limits — it is not a firehose/bulk scraper
and will not retrieve the full volume of a tool like the old Pushshift. For a
personal watchlist of a few subreddits and tickers, this is sufficient.
