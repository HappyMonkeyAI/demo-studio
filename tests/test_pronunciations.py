from __future__ import annotations

import json
from pathlib import Path

import pytest

from demo_studio.beats import validate_beats
from demo_studio.narrate import apply_pronunciations, load_lexicon, narrate_beats


def test_whole_word_case_insensitive() -> None:
    m = {"live": "lyve"}
    assert apply_pronunciations("Live in two weeks, live demo.", m) == "lyve in two weeks, lyve demo."
    assert apply_pronunciations("deliver, olive, lived", m) == "deliver, olive, lived"


def test_phrase_beats_word_and_hyphen_is_part_of_word() -> None:
    m = {"live": "lyve", "go-live": "go-lyve"}
    assert apply_pronunciations("defects at go-live", m) == "defects at go-lyve"
    assert apply_pronunciations("defects at go-live", {"live": "lyve"}) == "defects at go-live"


def test_empty_mapping_is_identity() -> None:
    assert apply_pronunciations("unchanged", {}) == "unchanged"


def test_schema_accepts_pronunciations() -> None:
    data = {"version": 1, "product": "p", "pronunciations": {"go-live": "go-lyve"}, "beats": [{"id": "a", "narration": "x"}]}
    assert validate_beats(data) == []
    data["pronunciations"] = {"go-live": 1}
    assert validate_beats(data)


def test_load_lexicon_rejects_non_strings(tmp_path: Path) -> None:
    p = tmp_path / "lex.json"
    p.write_text(json.dumps({"a": 1}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_lexicon(p)


class _FakeAdapter:
    def __init__(self) -> None:
        self.sent: list[str] = []

    def check_health(self) -> dict:
        return {"status": "ready", "provider": "fake"}

    def synthesize_wav(self, text: str) -> bytes:
        self.sent.append(text)
        return b"RIFF"


def test_narrate_sends_respelled_text_but_keeps_caption_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import demo_studio.narrate as narrate

    fake = _FakeAdapter()
    monkeypatch.setattr(narrate, "_make_adapter", lambda provider, voice=None: fake)
    monkeypatch.setattr(narrate, "_wav_duration_ms", lambda path: 1000)
    data = {
        "version": 1,
        "product": "p",
        "pronunciations": {"go-live": "go-lyve"},
        "beats": [{"id": "a", "narration": "Zero defects at go-live."}],
    }
    manifest = narrate_beats(data, tmp_path, lexicon={"defects": "dee-fects"})
    assert fake.sent == ["Zero dee-fects at go-lyve."]
    assert manifest["cues"][0]["text"] == "Zero defects at go-live."
    assert manifest["cues"][0]["spoken"] == "Zero dee-fects at go-lyve."
