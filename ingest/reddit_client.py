"""Pulls recent posts and top-level comments from configured subreddits
via Reddit's official API (PRAW). Read-only — never posts, votes, or
modifies anything on Reddit.

Does not retain Redditor usernames: only the post/comment id, subreddit,
text, score, and permalink are captured.
"""
from dataclasses import dataclass
from datetime import datetime, timezone

import praw

from config.settings import get_reddit_credentials


@dataclass
class RedditItem:
    item_id: str
    kind: str  # "post" or "comment"
    subreddit: str
    title: str | None
    body: str
    created_utc: datetime
    permalink: str
    score: int


def get_reddit_instance() -> praw.Reddit:
    creds = get_reddit_credentials()
    return praw.Reddit(
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        user_agent=creds["user_agent"],
        read_only=True,
    )


def fetch_recent_items(
    reddit: praw.Reddit,
    subreddits: list[str],
    post_limit: int = 50,
    comments_per_post: int = 20,
) -> list[RedditItem]:
    """Fetch recent posts (and their top-level comments) from each subreddit."""
    items: list[RedditItem] = []

    for sub_name in subreddits:
        subreddit = reddit.subreddit(sub_name)
        for post in subreddit.new(limit=post_limit):
            items.append(
                RedditItem(
                    item_id=post.id,
                    kind="post",
                    subreddit=sub_name,
                    title=post.title,
                    body=post.selftext or "",
                    created_utc=datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
                    permalink=f"https://reddit.com{post.permalink}",
                    score=post.score,
                )
            )

            if comments_per_post > 0:
                post.comments.replace_more(limit=0)
                for comment in post.comments[:comments_per_post]:
                    items.append(
                        RedditItem(
                            item_id=comment.id,
                            kind="comment",
                            subreddit=sub_name,
                            title=None,
                            body=comment.body or "",
                            created_utc=datetime.fromtimestamp(
                                comment.created_utc, tz=timezone.utc
                            ),
                            permalink=f"https://reddit.com{comment.permalink}",
                            score=comment.score,
                        )
                    )

    return items
