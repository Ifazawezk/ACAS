"""
Compare the offline analyzer from before the rewrite with the current one on the held-out
half, comment by comment, with `qabtest compare` from qatar-abtest.

    pip install -r requirements-eval.txt
    python tools/evaluate_analyzer.py --split test     # the current analyzer, data/eval/cases-test.csv
    python tools/compare_analyzers.py

The first run checks out commit dcfde55 (the last one before "Rewrite the offline analyzer
for English and Arabic") in a temporary git worktree, runs today's evaluator there on the
data already in data/eval, saves data/eval/cases-test-old.csv and removes the worktree.
Nothing is downloaded when data/eval is in place. --rerun makes it run the old analyzer again.

For each dataset it compares two right-or-wrong scores per comment: correct (the sentiment
matches the label) and ticket (a ticket opened exactly when the comment is labelled negative).
qabtest prints McNemar's test, a 95% paired bootstrap interval for the change and a
permutation p-value.

--data-issues prints the evaluator's figures for both versions with and without the comments
that data/checks flags: reviews in the Arabic sets with no Arabic letters, and texts that the
data gives more than one label.
"""
import argparse
import csv
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate_analyzer as evaluate  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "eval"
OLD_COMMIT = "dcfde55"
DATA_FOLDERS = ("airline", "arabic-prod", "arabic-res")


def run_old_analyzer(out: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "acas-old"
        subprocess.run(["git", "worktree", "add", "--detach", str(tree), OLD_COMMIT], cwd=PROJECT_ROOT, check=True)
        try:
            old_root = tree / PROJECT_ROOT.name
            shutil.copy(PROJECT_ROOT / "tools" / "evaluate_analyzer.py", old_root / "tools" / "evaluate_analyzer.py")
            for folder in DATA_FOLDERS:
                shutil.copytree(DATA_DIR / folder, old_root / "data" / "eval" / folder)
            subprocess.run(
                [sys.executable, "tools/evaluate_analyzer.py", "--split", "test", "--cases", str(out)],
                cwd=old_root, check=True,
            )
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(tree)], cwd=PROJECT_ROOT, check=True)


def scores(cases: Path) -> dict[str, list[dict]]:
    """One row per comment with 0/1 scores, grouped by dataset."""
    by_dataset = {}
    with open(cases, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            by_dataset.setdefault(row["dataset"], []).append({
                "id": row["id"],
                "correct": int(row["gold"] == row["predicted"]),
                "ticket": int(row["ticket_gold"] == row["ticket_predicted"]),
            })
    return by_dataset


def write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "correct", "ticket"])
        writer.writeheader()
        writer.writerows(rows)


def has_arabic_letter(text: str) -> bool:
    return any(unicodedata.category(c).startswith("L") and "ARABIC" in unicodedata.name(c, "") for c in text)


def data_issues() -> dict[str, set[str]]:
    """Case ids of texts the data gives more than one label, and of reviews in the Arabic sets
    with no Arabic letters."""
    csv.field_size_limit(10_000_000)
    flagged = {"two labels": set(), "no Arabic": set()}
    for name, spec in evaluate.DATASETS.items():
        labels = {}
        with open(evaluate.fetch(spec), encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                text, label = row[spec["text"]].strip(), spec["labels"].get(row[spec["label"]])
                if text and label:
                    labels.setdefault(text, set()).add(label)
        for text, found in labels.items():
            if len(found) > 1:
                flagged["two labels"].add(evaluate.case_id(name, text))
            if name.startswith("arabic") and not has_arabic_letter(text):
                flagged["no Arabic"].add(evaluate.case_id(name, text))
    return flagged


def print_with_and_without(label: str, cases: Path, flagged: dict[str, set[str]]) -> None:
    with open(cases, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    both = flagged["two labels"] | flagged["no Arabic"]
    for name in evaluate.DATASETS:
        for title, left_out in ((f"{label} {name}", set()), ("  without two labels", flagged["two labels"]),
                                ("  without both", both)):
            part = [r for r in rows if r["dataset"] == name and r["id"] not in left_out]
            figures = evaluate.score([r["gold"] for r in part], [r["predicted"] for r in part],
                                     [r["ticket_predicted"] == "1" for r in part])
            print(evaluate.format_row(title, figures))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--old", type=Path, default=DATA_DIR / "cases-test-old.csv")
    parser.add_argument("--new", type=Path, default=DATA_DIR / "cases-test.csv")
    parser.add_argument("--rerun", action="store_true", help="run the old analyzer again")
    parser.add_argument("--data-issues", action="store_true", help="figures with and without the flagged comments")
    args = parser.parse_args()
    if not args.new.exists():
        raise SystemExit(f"{args.new} is missing. Run: python tools/evaluate_analyzer.py --split test")
    if args.rerun or not args.old.exists():
        run_old_analyzer(args.old)

    sys.stdout.reconfigure(encoding="utf-8")
    if args.data_issues:
        flagged = data_issues()
        print(f"{'':22s} {'n':>7s} {'acc':>7s} {'macroF1':>7s} {'tickets':>7s} {'t.prec':>7s} {'t.rec':>7s} {'t.F1':>7s}")
        print_with_and_without("old", args.old, flagged)
        print_with_and_without("new", args.new, flagged)
        return

    old, new = scores(args.old), scores(args.new)
    with tempfile.TemporaryDirectory() as tmp:
        for dataset in new:
            folder = Path(tmp) / dataset
            write(folder / "old.csv", old[dataset])
            write(folder / "new.csv", new[dataset])
            for metric in ("correct", "ticket"):
                print(f"== {dataset}, {metric}", flush=True)
                subprocess.run(
                    [sys.executable, "-m", "qatar_abtest", "compare", str(folder / "old.csv"), str(folder / "new.csv"),
                     "--metric", metric],
                    check=True,
                )
                print(flush=True)


if __name__ == "__main__":
    main()
