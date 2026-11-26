from pathlib import Path

from demo_studio.beats import load_beats, validate_beats

ROOT = Path(__file__).resolve().parents[1]


def test_astro_cms_beats_valid():
    data = load_beats(ROOT / "demos" / "astro-cms" / "demo.beats.json")
    assert validate_beats(data) == []


def test_missing_version_fails():
    errors = validate_beats({"product": "x", "beats": [{"id": "a", "narration": "hi"}]})
    assert errors


from demo_studio.beats import validate_visuals, visual_kind

def _clip_beat(**vis):
    b = {"id": "c1", "narration": "hi", "visual": {"kind": "clip", **vis}}
    return {"version": 1, "product": "p", "beats": [b]}

def test_visual_kind_defaults_capture():
    assert visual_kind({"id": "a", "narration": "x"}) == "capture"
    assert visual_kind({"id": "a", "narration": "x", "visual": {"kind": "clip", "file": "f.mp4"}}) == "clip"

def test_clip_beat_passes_schema(tmp_path):
    from demo_studio.beats import validate_beats
    data = _clip_beat(file="f.mp4", in_sec=1.5, out_sec=9.0)
    assert validate_beats(data) == []
    (tmp_path / "f.mp4").write_bytes(b"")
    assert validate_visuals(data, tmp_path) == []

def test_clip_missing_file_and_bad_range(tmp_path):
    assert any("requires visual.file" in e for e in validate_visuals(_clip_beat(), tmp_path))
    (tmp_path / "f.mp4").write_bytes(b"")
    assert any("not found" in e for e in validate_visuals(_clip_beat(file="nope.mp4"), tmp_path))
    assert any("out_sec" in e for e in validate_visuals(_clip_beat(file="f.mp4", in_sec=5, out_sec=5), tmp_path))
    assert any("extension" in e for e in validate_visuals(_clip_beat(file="f.txt"), tmp_path))

def test_clip_with_actions_fails(tmp_path):
    data = _clip_beat(file="f.mp4")
    data["beats"][0]["actions"] = [{"type": "navigate", "url": "http://x"}]
    (tmp_path / "f.mp4").write_bytes(b"")
    assert any("actions" in e for e in validate_visuals(data, tmp_path))

def test_clip_path_expands_user_home(tmp_path):
    """`~/...` clip paths resolve against the home directory, not the pack dir."""
    from demo_studio.beats import resolve_clip_path
    beat = {"id": "c", "narration": "hi",
            "visual": {"kind": "clip", "file": "~/Videos/clip.mp4"}}
    assert resolve_clip_path(beat, tmp_path) == Path.home() / "Videos" / "clip.mp4"

def test_validate_visuals_reports_expanded_home_path(tmp_path):
    data = {"version": 1, "product": "p", "beats": [{
        "id": "c", "narration": "hi",
        "visual": {"kind": "clip", "file": "~/no-such-clip.mp4"}}]}
    errors = validate_visuals(data, tmp_path)
    assert any("~" not in e and str(Path.home()) in e for e in errors)
