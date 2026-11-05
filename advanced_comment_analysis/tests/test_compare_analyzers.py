"""The comparison turns the evaluator's rows into the 0/1 scores that McNemar's test needs."""
import csv
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parent.parent / "tools" / "compare_analyzers.py"
_spec = importlib.util.spec_from_file_location("compare_analyzers", _path)
compare = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(compare)


def test_scores_mark_sentiment_and_ticket_decisions(tmp_path):
    cases = tmp_path / "cases.csv"
    rows = [
        ("airline", "a1", "negative", "negative", 1, 1),
        ("airline", "a2", "neutral", "negative", 0, 1),
        ("arabic-products", "p1", "positive", "neutral", 0, 0),
    ]
    with open(cases, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["dataset", "id", "gold", "predicted", "ticket_gold", "ticket_predicted"])
        writer.writerows(rows)

    scores = compare.scores(cases)
    assert scores["airline"] == [{"id": "a1", "correct": 1, "ticket": 1}, {"id": "a2", "correct": 0, "ticket": 0}]
    assert scores["arabic-products"] == [{"id": "p1", "correct": 0, "ticket": 1}]


def test_arabic_letters_are_found_and_digits_do_not_count():
    assert compare.has_arabic_letter("المنتج جيد")
    assert compare.has_arabic_letter("good منتج")
    assert not compare.has_arabic_letter("i like it")
    assert not compare.has_arabic_letter("١٢٣ 014654109")
