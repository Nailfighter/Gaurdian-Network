import json
from pathlib import Path

from agents.reasoning_engine import evaluate_request


DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "urls.json"


def score_to_label(score: int) -> str:
    if score >= 70:
        return "Harmful"
    if score >= 40:
        return "Borderline"
    return "Educational"


def test_reasoning_accuracy_on_seed_dataset() -> None:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    total = 0
    correct = 0
    borderline_total = 0
    borderline_correct = 0

    for sample in dataset:
        result = evaluate_request(
            url=sample["url"],
            user_age=sample["user_age"],
            request_context=sample.get("context", ""),
            timestamp="2026-03-29T00:00:00Z",
        )
        predicted_label = score_to_label(int(result["decision_score"]))

        total += 1
        if predicted_label == sample["label"]:
            correct += 1

        if sample["label"] == "Borderline":
            borderline_total += 1
            if predicted_label == sample["label"]:
                borderline_correct += 1

    assert total == 30
    assert correct / total >= 0.75
    assert borderline_total > 0
    assert borderline_correct / borderline_total >= 0.70
