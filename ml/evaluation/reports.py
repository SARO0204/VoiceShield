"""
Evaluation Reporting Engine for VoiceShield.
Generates structured JSON and formatted summaries of model performance metrics.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("voiceshield.reports")


class EvaluationReporter:
    """
    Formats, persists, and exports anti-spoofing evaluation reports.
    """

    def __init__(self, reports_dir: str = "./reports"):
        self.reports_dir = reports_dir
        os.makedirs(self.reports_dir, exist_ok=True)

    def generate_report(
        self,
        model_metadata: Dict[str, Any],
        metrics: Dict[str, Any],
        dataset_info: Dict[str, Any],
        report_name: str = "model_evaluation.json",
    ) -> str:
        """
        Creates comprehensive evaluation report JSON.
        """
        report_data = {
            "model": {
                "name": model_metadata.get("model_name", "AASIST"),
                "version": model_metadata.get("model_version", "1.0"),
                "parameters": model_metadata.get("trainable_parameters", 0),
                "checkpoint": model_metadata.get("checkpoint_file", "best_model.pth"),
            },
            "dataset": dataset_info,
            "metrics": {
                "accuracy": metrics.get("accuracy", 0.0),
                "precision": metrics.get("precision", 0.0),
                "recall": metrics.get("recall", 0.0),
                "f1_score": metrics.get("f1", 0.0),
                "roc_auc": metrics.get("roc_auc", 0.0),
                "eer": metrics.get("eer", 0.0),
                "eer_threshold": metrics.get("eer_threshold", 0.5),
                "fpr": metrics.get("fpr", 0.0),
                "fnr": metrics.get("fnr", 0.0),
            },
            "confusion_matrix": metrics.get("confusion_matrix", {}),
            "thresholds": {
                "classification_threshold": metrics.get("threshold", 0.5),
                "uncertainty_range": [0.45, 0.55],
            },
            "generated_at": model_metadata.get("created_at", "N/A"),
        }

        report_path = os.path.join(self.reports_dir, report_name)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"Evaluation report written to '{report_path}'")
        return report_path
