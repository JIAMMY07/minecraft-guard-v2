from __future__ import annotations

from minecraft_guard.cli import audit_dataset


def test_dataset_audit_separates_labels_and_reports_metrics(config) -> None:
    report = audit_dataset(config.labels_dir)
    assert "missing_states" in report
    assert "false_positive_count" in report
    assert "false_negative_count" in report
