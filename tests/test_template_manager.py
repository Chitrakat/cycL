from __future__ import annotations

import json
import os

from generators.template_manager import get_template, load_templates


def test_load_templates_creates_file(tmp_path, monkeypatch):
    template_path = tmp_path / "workout_templates.json"
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()

    sample = {
        "video_id": "x",
        "workout_type": "HIIT",
        "duration_minutes": 30,
        "intervals": [
            {
                "duration_seconds": 60,
                "zone": "main set",
                "power_level": "7/10",
                "cadence_rpm": 90,
            }
        ],
    }
    with open(processed_dir / "sample.json", "w", encoding="utf-8") as handle:
        json.dump(sample, handle)

    monkeypatch.setattr(
        "generators.pattern_analyzer.DEFAULT_PROCESSED_GLOB",
        str(processed_dir / "*.json"),
    )
    monkeypatch.setattr(
        "generators.pattern_analyzer.DEFAULT_TEMPLATES_PATH",
        str(template_path),
    )
    monkeypatch.setattr(
        "generators.template_manager.DEFAULT_TEMPLATES_PATH",
        str(template_path),
    )

    payload = load_templates(str(template_path))
    assert payload["templates"]["HIIT"]

    template = get_template("HIIT", 30, str(template_path))
    assert template is not None
