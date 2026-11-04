"""The evaluation has to be right before its numbers mean anything."""
import csv
import importlib.util
from pathlib import Path

import pytest

_path = Path(__file__).resolve().parent.parent / "tools" / "evaluate_analyzer.py"
_spec = importlib.util.spec_from_file_location("evaluate_analyzer", _path)
evaluate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(evaluate)


def test_split_is_stable_and_about_even():
    texts = [f"comment number {i}" for i in range(4000)]
    first = [evaluate.split_of(t) for t in texts]
    assert first == [evaluate.split_of(t) for t in texts]
    assert 0.45 < first.count("dev") / len(first) < 0.55


def test_perfect_predictions_score_one():
    gold = ["negative", "neutral", "positive"]
    s = evaluate.score(gold, gold, [True, False, False])
    assert s["accuracy"] == 1.0
    assert s["macro_f1"] == 1.0
    assert s["ticket_precision"] == 1.0
    assert s["ticket_recall"] == 1.0


def test_always_negative_cannot_hide_behind_accuracy():
    gold = ["negative"] * 6 + ["positive"] * 4
    s = evaluate.score(gold, ["negative"] * 10, [True] * 10)
    assert s["accuracy"] == pytest.approx(0.6)
    assert s["macro_f1"] == pytest.approx(0.375)
    assert s["ticket_precision"] == pytest.approx(0.6)
    assert s["ticket_recall"] == 1.0


def test_macro_f1_ignores_a_class_the_data_does_not_have():
    gold = ["negative", "positive"]
    assert evaluate.score(gold, gold, [True, False])["macro_f1"] == 1.0


def test_every_analyzer_emotion_has_a_sentiment():
    from app.services.openai_client import analyze_sentiment_locally

    for text in ("I love it", "This is terrible and I hate it", "ok", "شكرا", "?"):
        assert analyze_sentiment_locally(text)["emotion"] in evaluate.EMOTION_TO_SENTIMENT


def test_confidence_bands_report_the_share_correct():
    gold = ["negative", "negative", "positive"]
    predicted = ["negative", "positive", "positive"]
    assert evaluate.confidence_bands(gold, predicted, [0.55, 0.55, 0.9]) == "0.5-0.60: 50% of 2  0.8-0.95: 100% of 1"


def test_mistakes_of_the_test_half_cannot_be_printed(monkeypatch):
    monkeypatch.setattr("sys.argv", ["evaluate_analyzer.py", "--split", "test", "--errors", "5"])
    with pytest.raises(SystemExit, match="spoil"):
        evaluate.main()


def run_on_tiny_data(monkeypatch, argv, results):
    rows = [("I hate it", "negative"), ("Lovely", "positive"), ("ok", "neutral")]
    monkeypatch.setattr(evaluate, "DATASETS", {"tiny": {}})
    monkeypatch.setattr(evaluate, "load", lambda name, split: rows)
    monkeypatch.setattr(evaluate, "analyze", lambda text: results[text])
    monkeypatch.setattr("sys.argv", ["evaluate_analyzer.py", *argv])
    evaluate.main()


def read_cases(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_each_comment_is_saved_so_two_runs_can_be_paired(monkeypatch, tmp_path):
    first, second = tmp_path / "first.csv", tmp_path / "second.csv"
    run_on_tiny_data(monkeypatch, ["--cases", str(first)], {
        "I hate it": ("negative", True, 0.9), "Lovely": ("negative", True, 0.6), "ok": ("neutral", False, 0.5),
    })
    run_on_tiny_data(monkeypatch, ["--cases", str(second)], {
        "I hate it": ("negative", False, 0.9), "Lovely": ("positive", False, 0.9), "ok": ("neutral", False, 0.5),
    })

    cases = read_cases(first)
    assert [(c["dataset"], c["gold"], c["predicted"], c["ticket_gold"], c["ticket_predicted"]) for c in cases] == [
        ("tiny", "negative", "negative", "1", "1"),
        ("tiny", "positive", "negative", "0", "1"),
        ("tiny", "neutral", "neutral", "0", "0"),
    ]
    ids = [c["id"] for c in cases]
    assert len(set(ids)) == 3
    assert [c["id"] for c in read_cases(second)] == ids
    assert [c["predicted"] for c in read_cases(second)] == ["negative", "positive", "neutral"]


def test_cases_go_to_the_ignored_data_folder_by_default(monkeypatch, tmp_path):
    monkeypatch.setattr(evaluate, "DATA_DIR", tmp_path)
    run_on_tiny_data(monkeypatch, ["--split", "test"], {
        "I hate it": ("negative", True, 0.9), "Lovely": ("positive", False, 0.9), "ok": ("neutral", False, 0.5),
    })
    assert len(read_cases(tmp_path / "cases-test.csv")) == 3
