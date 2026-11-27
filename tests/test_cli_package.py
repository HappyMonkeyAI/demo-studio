from __future__ import annotations

import argparse
from pathlib import Path

from demo_studio import cli


def _args(run_dir: Path, **overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "run_dir": str(run_dir),
        "look": "clean",
        "beats": None,
        "title_card": None,
        "subtitle": "",
        "voice_after_title": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_parser_accepts_merged_package_options() -> None:
    args = cli.build_parser().parse_args(
        ["package", "run", "--beats", "demo.beats.json", "--voice-after-title"]
    )

    assert args.beats == "demo.beats.json"
    assert args.voice_after_title is True


def test_package_forwards_title_voice_lead_in(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "picture.mp4").write_bytes(b"picture")
    captured: dict[str, object] = {}

    def fake_burn_title_card(picture: Path, polished: Path, **kwargs: object) -> None:
        polished.write_bytes(b"polished")

    def fake_mux_package(run_dir: Path, **kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"look": kwargs["look"]}

    monkeypatch.setattr(cli, "burn_title_card", fake_burn_title_card)
    monkeypatch.setattr(cli, "mux_package", fake_mux_package)

    result = cli._cmd_package(
        _args(tmp_path, title_card="Title", voice_after_title=True)
    )

    assert result == 0
    assert captured["lead_in_s"] == cli.TITLE_CARD_SECONDS


def test_package_beats_assembles_clip_picture_and_skips_studio(
    tmp_path: Path, monkeypatch
) -> None:
    beats_path = tmp_path / "demo.beats.json"
    narration = tmp_path / "narration" / "narration.json"
    narration.parent.mkdir()
    narration.write_text('{"cues": []}', encoding="utf-8")
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        cli,
        "load_beats",
        lambda path: {"beats": [{"id": "clip", "visual": {"kind": "clip", "file": "clip.mp4"}}]},
    )

    def fake_assemble_picture(data, cues, frames, run_dir, **kwargs):
        captured["assembled"] = True
        return {"segments": 1, "total_s": 1.0}

    def fake_compose_studio_mp4(run_dir: Path, picture: Path) -> None:
        raise AssertionError("studio compose must not run for clip packs")

    def fake_mux_package(run_dir: Path, **kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"look": kwargs["look"]}

    monkeypatch.setattr(cli, "assemble_picture", fake_assemble_picture)
    monkeypatch.setattr(cli, "compose_studio_mp4", fake_compose_studio_mp4)
    monkeypatch.setattr(cli, "mux_package", fake_mux_package)

    result = cli._cmd_package(_args(tmp_path, beats=str(beats_path), look="studio"))

    assert result == 0
    assert captured["assembled"] is True
    assert captured["look"] == "clean"
