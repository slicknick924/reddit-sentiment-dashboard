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

As of late 2025, Reddit closed self-service API app creation. New OAuth
clients require approval under Reddit's Responsible Builder Policy before
you can get a client ID/secret:

1. Submit a Data Access Request via Reddit's support form, selecting
   "I'm a developer" and describing the read-only, personal, non-commercial
   use case (see this repo's description for exactly what the app does).
2. Once approved, Reddit will direct you to create a **script**-type app
   to obtain a **client ID** and **client secret**.

This project does not interact with Reddit at all beyond reading public
posts/comments via the official API — no posting, voting, commenting, or
messaging.

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
