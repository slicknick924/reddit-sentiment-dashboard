"""Sentiment scoring using FinBERT, a BERT model fine-tuned on financial
text. Runs fully locally via Hugging Face `transformers` — no API calls,
no data leaves the machine.
"""
from dataclasses import dataclass
from functools import lru_cache

from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

MODEL_NAME = "ProsusAI/finbert"


@dataclass
class SentimentResult:
    label: str  # "positive", "negative", "neutral"
    score: float  # confidence of the predicted label, 0-1
    signed_score: float  # positive_prob - negative_prob, range -1..1


@lru_cache(maxsize=1)
def _load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()
    return tokenizer, model


def score_text(text: str) -> SentimentResult:
    text = (text or "").strip()
    if not text:
        return SentimentResult(label="neutral", score=1.0, signed_score=0.0)

    tokenizer, model = _load_model()
    inputs = tokenizer(
        text, return_tensors="pt", truncation=True, max_length=512, padding=True
    )
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]

    # FinBERT label order: 0=positive, 1=negative, 2=neutral
    labels = ["positive", "negative", "neutral"]
    probs_list = probs.tolist()
    best_idx = max(range(len(probs_list)), key=lambda i: probs_list[i])

    signed = probs_list[0] - probs_list[1]  # positive_prob - negative_prob

    return SentimentResult(
        label=labels[best_idx],
        score=probs_list[best_idx],
        signed_score=signed,
    )


def score_batch(texts: list[str]) -> list[SentimentResult]:
    return [score_text(t) for t in texts]
