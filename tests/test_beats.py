from pathlib import Path

from demo_studio.beats import load_beats, validate_beats

ROOT = Path(__file__).resolve().parents[1]


def test_astro_cms_beats_valid():
    data = load_beats(ROOT / "demos" / "astro-cms" / "demo.beats.json")
    assert validate_beats(data) == []


def test_missing_version_fails():
    errors = validate_beats({"product": "x", "beats": [{"id": "a", "narration": "hi"}]})
    assert errors
