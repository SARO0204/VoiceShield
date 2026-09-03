"""
Model Evaluation Metrics for Anti-Spoofing & Voice Deepfake Detection.
Calculates Accuracy, Precision, Recall, F1 Score, ROC-AUC, Confusion Matrix,
False Positive Rate, False Negative Rate, and Equal Error Rate (EER).
"""

from typing import Dict, Any, List, Tuple, Union, Optional
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    roc_curve,
)


def compute_eer(y_true: np.ndarray, y_scores: np.ndarray) -> Tuple[float, float]:
    """
    Computes Equal Error Rate (EER) and the optimal EER threshold.
    Args:
        y_true (np.ndarray): Binary ground truth (0 = bonafide, 1 = spoof)
        y_scores (np.ndarray): Predicted synthetic/spoof probabilities
    Returns:
        eer (float): Equal Error Rate (0.0 to 1.0)
        threshold (float): Threshold at which FPR approx equals FNR
    """
    if len(y_true) == 0 or len(np.unique(y_true)) < 2:
        return 0.0, 0.5

    fpr, tpr, thresholds = roc_curve(y_true, y_scores, pos_label=1)
    fnr = 1.0 - tpr

    # Find the threshold where FPR and FNR intersect
    idx = np.nanargmin(np.abs(fpr - fnr))
    eer = float((fpr[idx] + fnr[idx]) / 2.0)
    eer_threshold = float(thresholds[idx]) if idx < len(thresholds) else 0.5

    return round(eer, 4), round(eer_threshold, 4)


def compute_full_metrics(
    y_true: Union[List[int], np.ndarray],
    y_scores: Union[List[float], np.ndarray],
    threshold: float = 0.50,
) -> Dict[str, Any]:
    """
    Computes complete evaluation metrics suite for voice clone detection.
    """
    y_true_arr = np.array(y_true, dtype=int)
    y_scores_arr = np.array(y_scores, dtype=float)

    if len(y_true_arr) == 0:
        return {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "roc_auc": 0.0,
            "eer": 0.0,
            "eer_threshold": 0.5,
            "fpr": 0.0,
            "fnr": 0.0,
            "total_samples": 0,
            "confusion_matrix": {"tn": 0, "fp": 0, "fn": 0, "tp": 0},
        }

    y_pred = (y_scores_arr >= threshold).astype(int)

    acc = float(accuracy_score(y_true_arr, y_pred))
    prec = float(precision_score(y_true_arr, y_pred, zero_division=0))
    rec = float(recall_score(y_true_arr, y_pred, zero_division=0))
    f1 = float(f1_score(y_true_arr, y_pred, zero_division=0))

    try:
        auc = float(roc_auc_score(y_true_arr, y_scores_arr)) if len(np.unique(y_true_arr)) > 1 else 1.0
    except Exception:
        auc = 0.5

    eer, eer_thresh = compute_eer(y_true_arr, y_scores_arr)

    # Confusion matrix
    if len(np.unique(y_true_arr)) > 1:
        cm = confusion_matrix(y_true_arr, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
    else:
        # Fallback if only 1 class in sample batch
        tp = int(np.sum((y_true_arr == 1) & (y_pred == 1)))
        tn = int(np.sum((y_true_arr == 0) & (y_pred == 0)))
        fp = int(np.sum((y_true_arr == 0) & (y_pred == 1)))
        fn = int(np.sum((y_true_arr == 1) & (y_pred == 0)))

    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
    fnr = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "roc_auc": round(auc, 4),
        "eer": round(eer, 4),
        "eer_threshold": round(eer_thresh, 4),
        "fpr": round(fpr, 4),
        "fnr": round(fnr, 4),
        "threshold": round(threshold, 4),
        "total_samples": len(y_true_arr),
        "bonafide_count": int(np.sum(y_true_arr == 0)),
        "spoof_count": int(np.sum(y_true_arr == 1)),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
    }
