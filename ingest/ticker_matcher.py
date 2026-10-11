"""Extracts ticker mentions from free text, filtering ambiguous tickers
(common English words that also happen to be valid symbols) unless they
appear as an explicit cashtag like $IT.
"""
import re
from typing import Iterable


def build_ticker_pattern(tickers: Iterable[str]) -> re.Pattern:
    escaped = sorted((re.escape(t) for t in tickers), key=len, reverse=True)
    joined = "|".join(escaped)
    return re.compile(rf"\b({joined})\b", re.IGNORECASE)


def build_cashtag_pattern(tickers: Iterable[str]) -> re.Pattern:
    escaped = sorted((re.escape(t) for t in tickers), key=len, reverse=True)
    joined = "|".join(escaped)
    return re.compile(rf"\$({joined})\b", re.IGNORECASE)


def extract_mentions(text: str, tickers: list[str], ambiguous_tickers: set[str]) -> list[str]:
    """Return the list of tickers mentioned in `text`.

    Unambiguous tickers are matched as bare words. Ambiguous tickers (ones
    that collide with common English words) are only matched as cashtags
    (e.g. "$IT") to cut down on false positives.
    """
    if not text:
        return []

    unambiguous = [t for t in tickers if t.upper() not in ambiguous_tickers]
    ambiguous = [t for t in tickers if t.upper() in ambiguous_tickers]

    found = set()

    if unambiguous:
        pattern = build_ticker_pattern(unambiguous)
        found.update(m.upper() for m in pattern.findall(text))

    if ambiguous:
        cashtag_pattern = build_cashtag_pattern(ambiguous)
        found.update(m.upper() for m in cashtag_pattern.findall(text))

    # Also catch cashtags for unambiguous tickers in case someone writes $TSLA
    generic_cashtag = re.compile(r"\$([A-Za-z]{1,5})\b")
    for m in generic_cashtag.findall(text):
        upper = m.upper()
        if upper in {t.upper() for t in tickers}:
            found.add(upper)

    return sorted(found)
