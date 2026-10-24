import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def metrics(labels, scores, threshold):
    labels, scores = np.asarray(labels), np.asarray(scores)
    predicted = scores >= threshold
    matrix = confusion_matrix(labels, predicted, labels=[False, True])
    ece = 0.0
    for low in np.arange(0, 1, 0.1):
        selected = (scores >= low) & (scores < low + 0.1 if low < 0.9 else scores <= 1)
        if selected.any():
            ece += selected.mean() * abs(
                scores[selected].mean() - labels[selected].mean()
            )
    return {
        "accuracy": float(accuracy_score(labels, predicted)),
        "precision": float(precision_score(labels, predicted, zero_division=0)),
        "dangerous_recall": float(recall_score(labels, predicted, zero_division=0)),
        "f1": float(f1_score(labels, predicted, zero_division=0)),
        "confusion_matrix": matrix.tolist(),
        "confusion_order": ["survives", "fails"],
        "false_negatives": int(matrix[1, 0]),
        "pr_auc": float(average_precision_score(labels, scores))
        if len(np.unique(labels)) > 1
        else None,
        "roc_auc": float(roc_auc_score(labels, scores))
        if len(np.unique(labels)) > 1
        else None,
        "brier_score": float(brier_score_loss(labels, scores)),
        "ece_10_bins": float(ece),
        "threshold": float(threshold),
        "n": int(len(labels)),
    }


def choose_threshold(labels, scores):
    # Validation-only F2: dangerous false negatives have four times the F-score weight.
    candidates = np.linspace(0.02, 0.98, 97)

    def objective(t):
        p = precision_score(labels, scores >= t, zero_division=0)
        r = recall_score(labels, scores >= t, zero_division=0)
        return 5 * p * r / (4 * p + r) if p + r else 0

    return float(max(candidates, key=lambda t: (objective(t), -t)))
