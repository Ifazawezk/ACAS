"""
Measure the offline comment analyzer on real, labelled comments it was not written from.

    python tools/evaluate_analyzer.py                 # development half
    python tools/evaluate_analyzer.py --split test    # held-out half

The data is downloaded on first use into data/eval, which git ignores. It is not stored in
this repository because of its licences (see DATASETS below).

Each comment goes to the development half or the test half according to a hash of its text.
The split is the same on every run, and identical comments can never land in both halves.
Rules are written and tuned on the development half only. The test half is for the final
figures, so looking at its errors would make those figures worthless.

The datasets label sentiment, so that is what can be measured here:
    joy is counted as positive, neutral as neutral, sadness and anger as negative.
A comment labelled negative is treated as one that should open a ticket.
Intent and priority have no labels and are not measured.
"""
import argparse
import csv
import hashlib
import os
import sys
import urllib.request
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ["FORCE_LOCAL"] = "true"

DATA_DIR = PROJECT_ROOT / "data" / "eval"
CLASSES = ("negative", "neutral", "positive")
EMOTION_TO_SENTIMENT = {"joy": "positive", "neutral": "neutral", "sadness": "negative", "anger": "negative"}
CONFIDENCE_BANDS = ((0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 1.0))

DATASETS = {
    "airline": {
        "title": "Twitter US Airline Sentiment, English tweets to airlines, human labels, CC BY-NC-SA 4.0",
        "url": "https://huggingface.co/datasets/osanseviero/twitter-airline-sentiment/resolve/main/Tweets.csv",
        "file": "airline/Tweets.csv",
        "sha256": "ea94b23f41892b290dec3330bb8cf9cb6b8bc669eaae5f3a84c40f7b0de8f15e",
        "text": "text",
        "label": "airline_sentiment",
        "labels": {"negative": "negative", "neutral": "neutral", "positive": "positive"},
    },
    "arabic-products": {
        "title": "ElSahar and El-Beltagy 2015, Arabic souq.com product reviews, labels taken from star ratings",
        "url": "https://raw.githubusercontent.com/hadyelsahar/large-arabic-sentiment-analysis-resouces/master/datasets/PROD.csv",
        "file": "arabic-prod/PROD.csv",
        "sha256": "b2b1c98b7fc180f2ad447c948efdc38bb96b53ee6966bf677f7485d089a6d298",
        "text": "text",
        "label": "polarity",
        "labels": {"-1": "negative", "0": "neutral", "1": "positive"},
    },
    "arabic-restaurants": {
        "title": "ElSahar and El-Beltagy 2015, Arabic qaym.com restaurant reviews, labels taken from star ratings, no neutral class",
        "url": "https://raw.githubusercontent.com/hadyelsahar/large-arabic-sentiment-analysis-resouces/master/datasets/RES1.csv",
        "file": "arabic-res/RES1.csv",
        "sha256": "afdb587d41310302372ed154a91a7231f566c137cadeea9df166e7326c2c4b19",
        "text": "text",
        "label": "polarity",
        "labels": {"-1": "negative", "1": "positive"},
    },
}


def split_of(text: str) -> str:
    """Send a comment to one half for good, based only on its text."""
    return "dev" if hashlib.sha256(text.encode("utf-8")).digest()[0] < 128 else "test"


def fetch(spec: dict) -> Path:
    path = DATA_DIR / spec["file"]
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {spec['url']}", file=sys.stderr)
        urllib.request.urlretrieve(spec["url"], path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != spec["sha256"]:
        raise SystemExit(f"{path} does not match the expected checksum, so results would not be comparable")
    return path


def load(name: str, split: str) -> list[tuple[str, str]]:
    """Return (text, label) pairs for one half of a dataset, with duplicate texts removed."""
    spec = DATASETS[name]
    csv.field_size_limit(10_000_000)
    seen = set()
    rows = []
    with open(fetch(spec), encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            text = row[spec["text"]].strip()
            label = spec["labels"].get(row[spec["label"]])
            if text and label and text not in seen and split_of(text) == split:
                seen.add(text)
                rows.append((text, label))
    return rows


def f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def ratio(part: float, whole: float) -> float:
    return part / whole if whole else 0.0


def score(gold: list[str], predicted: list[str], tickets: list[bool]) -> dict:
    """Accuracy, macro F1 over the classes the data has, and how good the ticket decision is."""
    classes = [c for c in CLASSES if c in gold]
    f1_scores = []
    for c in classes:
        true_positive = sum(g == c and p == c for g, p in zip(gold, predicted))
        precision = ratio(true_positive, sum(p == c for p in predicted))
        recall = ratio(true_positive, sum(g == c for g in gold))
        f1_scores.append(f1(precision, recall))

    true_tickets = sum(g == "negative" and t for g, t in zip(gold, tickets))
    ticket_precision = ratio(true_tickets, sum(tickets))
    ticket_recall = ratio(true_tickets, sum(g == "negative" for g in gold))
    return {
        "comments": len(gold),
        "accuracy": ratio(sum(g == p for g, p in zip(gold, predicted)), len(gold)),
        "macro_f1": sum(f1_scores) / len(f1_scores),
        "ticket_rate": ratio(sum(tickets), len(gold)),
        "ticket_precision": ticket_precision,
        "ticket_recall": ticket_recall,
        "ticket_f1": f1(ticket_precision, ticket_recall),
    }


def analyze(text: str) -> tuple[str, bool, float]:
    from app.services.openai_client import analyze_sentiment_locally

    result = analyze_sentiment_locally(text)
    return EMOTION_TO_SENTIMENT[result["emotion"]], bool(result["needs_ticket"]), result["confidence"]


def confidence_bands(gold: list[str], predicted: list[str], confidence: list[float]) -> str:
    """Share of correct answers at each confidence level. Confidence is not a probability."""
    parts = []
    for low, high in CONFIDENCE_BANDS:
        hits = [g == p for g, p, c in zip(gold, predicted, confidence) if low <= c < high]
        if hits:
            parts.append(f"{low:.1f}-{min(high, 0.95):.2f}: {ratio(sum(hits), len(hits)):.0%} of {len(hits)}")
    return "  ".join(parts)


def format_row(name: str, s: dict) -> str:
    return (
        f"{name:22s} {s['comments']:>7d} {s['accuracy']:>7.1%} {s['macro_f1']:>7.3f} "
        f"{s['ticket_rate']:>7.1%} {s['ticket_precision']:>7.1%} {s['ticket_recall']:>7.1%} {s['ticket_f1']:>7.3f}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--split", choices=("dev", "test"), default="dev")
    parser.add_argument("--errors", type=int, default=0, help="print this many mistakes (development half only)")
    args = parser.parse_args()
    if args.errors and args.split == "test":
        raise SystemExit("Reading the test half's mistakes would spoil it. Use the development half.")

    sys.stdout.reconfigure(encoding="utf-8")
    print(f"half: {args.split}")
    print(f"{'':22s} {'n':>7s} {'acc':>7s} {'macroF1':>7s} {'tickets':>7s} {'t.prec':>7s} {'t.rec':>7s} {'t.F1':>7s}")
    for name in DATASETS:
        rows = load(name, args.split)
        gold = [label for _, label in rows]
        results = [analyze(text) for text, _ in rows]
        predicted = [sentiment for sentiment, _, _ in results]
        tickets = [ticket for _, ticket, _ in results]
        confidence = [value for _, _, value in results]

        majority = Counter(gold).most_common(1)[0][0]
        print(format_row(f"{name}: always {majority[:3]}", score(gold, [majority] * len(gold), [majority == "negative"] * len(gold))))
        print(format_row(f"{name}: analyzer", score(gold, predicted, tickets)))
        print(f"    correct by confidence: {confidence_bands(gold, predicted, confidence)}")

        if args.errors:
            mistakes = [(g, p, t) for (t, g), p in zip(rows, predicted) if g != p]
            for g, p, t in mistakes[: args.errors]:
                print(f"    gold={g[:3]} got={p[:3]} {t[:110]!r}")


if __name__ == "__main__":
    main()
