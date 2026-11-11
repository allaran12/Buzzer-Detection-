#!/usr/bin/env python3
"""Retrain the Phase 6 fusion proxy on canonical Batch 2/3 features."""
from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from models.phase6_advanced import (
    BATCHES,
    MODEL_FEATURES,
    SEQUENCE_FEATURES,
    GRAPH_FEATURES,
    build_pipeline,
    dependency_status,
    evaluate_cross_issue,
    evaluate_group_cv,
    explain_full_model,
    find_repo_root,
    load_training_data,
    save_confusion_matrix,
)


BRANCHES = {
    "text_proxy": "text",
    "temporal_proxy": "temporal",
    "graph_proxy": "graph",
    "fusion_proxy": "fusion",
}


def _experiment_paths(root: Path, experiment: str) -> tuple[Path, Path]:
    output_dir = root / "output" / "phase6_canonical" / experiment
    model_dir = root / "models"
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    return output_dir, model_dir


def run_experiment(root: str | Path | None, experiment: str, batches: tuple[str, ...]) -> dict[str, Any]:
    root_path = find_repo_root(root)
    output_dir, model_dir = _experiment_paths(root_path, experiment)
    data, _, readiness = load_training_data(root_path, batches)
    metric_rows = []
    oof_frames = []
    confusion_by_branch = {}
    for model_name, branch in BRANCHES.items():
        metrics, oof = evaluate_group_cv(data, branch)
        metric_rows.append({
            "experiment": experiment,
            "model": model_name,
            **{key: value for key, value in metrics.items() if key != "confusion_matrix"},
        })
        oof["experiment"] = experiment
        oof["model"] = model_name
        oof_frames.append(oof)
        confusion_by_branch[model_name] = metrics["confusion_matrix"]

    metrics_frame = pd.DataFrame(metric_rows)
    metrics_frame.to_csv(output_dir / "phase6_group_cv_metrics.csv", index=False)
    pd.concat(oof_frames, ignore_index=True).to_csv(
        output_dir / "phase6_group_cv_oof_predictions.csv", index=False
    )

    cross_issue = pd.DataFrame()
    if set(batches) == set(BATCHES):
        cross_issue = evaluate_cross_issue(data, "fusion")
        cross_issue.insert(0, "experiment", experiment)
        cross_issue.to_csv(output_dir / "phase6_cross_issue_metrics.csv", index=False)

    fusion_model = build_pipeline("fusion")
    fusion_model.fit(data, data["label"].astype(int))
    model_filename = f"phase6_fusion_proxy_{experiment}_canonical.pkl"
    artifact = {
        "model": fusion_model,
        "feature_columns": MODEL_FEATURES,
        "sequence_features": SEQUENCE_FEATURES,
        "graph_features": GRAPH_FEATURES,
        "training_rows": int(len(data)),
        "training_batches": sorted(data["dataset_id"].unique().tolist()),
        "experiment": experiment,
        "schema_version": "canonical-v1",
        "random_seed": 42,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "text_backend": "tfidf_proxy",
        "advanced_backends": {"indobertweet": False, "lstm": False, "graphsage": False},
        "dependency_status": dependency_status(),
        "note": "Canonical Phase 6 fusion proxy; not an IndoBERTweet/LSTM/GraphSAGE model.",
    }
    model_path = model_dir / model_filename
    with model_path.open("wb") as handle:
        pickle.dump(artifact, handle)

    explanations = explain_full_model(fusion_model, data)
    explanations.to_csv(output_dir / "phase6_fusion_explanations.csv", index=False)
    errors = explanations[explanations["label"] != explanations["prediction"]].copy()
    errors["error_type"] = errors.apply(
        lambda row: "false_positive" if row["label"] == 0 and row["prediction"] == 1 else "false_negative",
        axis=1,
    )
    errors.to_csv(output_dir / "phase6_error_analysis.csv", index=False)

    for model_name, matrix in confusion_by_branch.items():
        save_confusion_matrix(
            matrix,
            output_dir / f"{model_name}_confusion_matrix.png",
            f"{experiment} - {model_name} - Canonical Group CV",
        )
    readiness_payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment": experiment,
        "batches": readiness,
        "training_rows": int(len(data)),
        "training_batches": sorted(data["dataset_id"].unique().tolist()),
        "labeled_single_post_accounts": int((data["sequence_len"] == 1).sum()),
        "model_path": str(model_path),
    }
    (output_dir / "phase6_readiness.json").write_text(
        json.dumps(readiness_payload, indent=2, default=str), encoding="utf-8"
    )
    return {
        "experiment": experiment,
        "batches": batches,
        "metrics": metrics_frame,
        "cross_issue": cross_issue,
        "readiness": readiness_payload,
        "model_path": model_path,
        "output_dir": output_dir,
    }


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    selected = frame[columns].copy()
    numeric = selected.select_dtypes(include="number").columns
    selected[numeric] = selected[numeric].round(3)
    return selected.to_markdown(index=False)


def write_comparison_report(root: str | Path, results: dict[str, dict[str, Any]]) -> Path:
    root_path = find_repo_root(root)
    rows = []
    phase5_path = root_path / "output" / "phase5" / "group_cv_metrics.csv"
    if phase5_path.exists():
        phase5 = pd.read_csv(phase5_path)
        for model_name in ["Combined RF", "Combined Logistic Regression"]:
            match = phase5[phase5["model"] == model_name]
            if not match.empty:
                row = match.iloc[0]
                rows.append({
                    "source": f"Phase 5 {model_name}",
                    **{key: row.get(key) for key in ["accuracy", "precision_buzzer", "recall_buzzer", "f1_buzzer", "roc_auc", "pr_auc"]},
                })
    phase6_path = root_path / "output" / "phase6" / "phase6_group_cv_metrics.csv"
    if phase6_path.exists():
        phase6 = pd.read_csv(phase6_path)
        match = phase6[phase6["model"] == "fusion_proxy"]
        if not match.empty:
            row = match.iloc[0]
            rows.append({
                "source": "Phase 6 fusion proxy (legacy features)",
                **{key: row.get(key) for key in ["accuracy", "precision_buzzer", "recall_buzzer", "f1_buzzer", "roc_auc", "pr_auc"]},
            })
    for experiment, result in results.items():
        match = result["metrics"][result["metrics"]["model"] == "fusion_proxy"]
        if not match.empty:
            row = match.iloc[0]
            rows.append({
                "source": f"Phase 6 canonical {experiment}",
                **{key: row.get(key) for key in ["accuracy", "precision_buzzer", "recall_buzzer", "f1_buzzer", "roc_auc", "pr_auc"]},
            })
    comparison = pd.DataFrame(rows)
    report_path = root_path / "reports" / "CANONICAL_MODEL_COMPARISON_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = [
        "# CoordinX - Canonical Model Comparison",
        "",
        f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## 1. Canonical data validation",
        "",
    ]
    for batch in BATCHES:
        validation = json.loads((root_path / "data" / "features" / f"{batch}_validation.json").read_text())
        report.extend([
            f"- `{batch}`: {validation['post']['posts']} posts, {validation['account_features']['rows']} accounts, "
            f"{validation['graph']['valid_edge_events']} valid edge events, "
            f"{validation['graph']['unique_directed_edges']} unique directed edges.",
            f"- Labels: {validation['labels']['label_counts']}; unmatched labels: {validation['labels']['unmatched_labels']}.",
        ])
    report.extend(["", "## 2. Group CV comparison", ""])
    if comparison.empty:
        report.append("No comparison metrics were available.")
    else:
        report.append(_markdown_table(comparison, ["source", "accuracy", "precision_buzzer", "recall_buzzer", "f1_buzzer", "roc_auc", "pr_auc"]))
    report.extend([
        "",
        "## 3. Cross-issue evaluation",
        "",
        "Cross-issue scores are reported only for the combined canonical experiment because batch-only models do not contain the other issue in their training artifact.",
        "",
    ])
    combined_cross = results.get("combined", {}).get("cross_issue", pd.DataFrame())
    if combined_cross is not None and not combined_cross.empty:
        report.append(_markdown_table(combined_cross, ["train_batch", "test_batch", "accuracy", "precision_buzzer", "recall_buzzer", "f1_buzzer", "roc_auc", "pr_auc"]))
    else:
        report.append("No canonical cross-issue metrics were generated.")
    report.extend([
        "",
        "## 4. Interpretation",
        "",
        "- Canonical features are regenerated from standardized data and use string-preserved IDs.",
        "- `buzzer_score` remains a heuristic review aid and is excluded from model features and ground truth.",
        "- All evaluations are account-level; no post-level random split is used.",
        "- The Phase 6 artifacts remain TF-IDF/temporal/graph proxy models because the active environment lacks the deep-learning backends.",
        "- Metrics are descriptive only: each batch has 50 manually labeled accounts and many accounts have one post.",
        "",
        "## 5. Artifacts",
        "",
        "- `data/features/batch2_*` and `data/features/batch3_*` canonical feature files",
        "- `data/labels/batch2_labeled_canonical.csv` and `data/labels/batch3_labeled_canonical.csv`",
        "- `models/phase6_fusion_proxy_batch2_canonical.pkl`",
        "- `models/phase6_fusion_proxy_batch3_canonical.pkl`",
        "- `models/phase6_fusion_proxy_combined_canonical.pkl`",
        "- `output/phase6_canonical/` per-experiment metrics, matrices, explanations, and readiness files",
    ])
    report_path.write_text("\n".join(report), encoding="utf-8")
    return report_path


def run_suite(root: str | Path | None = None) -> dict[str, dict[str, Any]]:
    root_path = find_repo_root(root)
    results = {
        "batch2": run_experiment(root_path, "batch2", ("batch2",)),
        "batch3": run_experiment(root_path, "batch3", ("batch3",)),
        "combined": run_experiment(root_path, "combined", BATCHES),
    }
    write_comparison_report(root_path, results)
    return results


if __name__ == "__main__":
    results = run_suite()
    for experiment, result in results.items():
        fusion = result["metrics"][result["metrics"]["model"] == "fusion_proxy"].iloc[0]
        print(
            f"{experiment}: accuracy={fusion['accuracy']:.3f}, "
            f"precision={fusion['precision_buzzer']:.3f}, "
            f"recall={fusion['recall_buzzer']:.3f}, "
            f"f1={fusion['f1_buzzer']:.3f}, roc_auc={fusion['roc_auc']:.3f}"
        )
