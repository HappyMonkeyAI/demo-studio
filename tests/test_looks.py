from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from demo_studio.looks import LOOK_PRESETS, apply_look, list_looks


def test_list_looks() -> None:
    assert "clean" in list_looks()
    assert "product-zoom" in list_looks()
    assert LOOK_PRESETS == list_looks()


def test_unknown_look_raises(tmp_path: Path) -> None:
    src = tmp_path / "picture.mp4"
    src.write_bytes(b"not-a-real-mp4")
    with pytest.raises(ValueError, match="unknown look"):
        apply_look(src, tmp_path / "out.mp4", look="recordly")


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg required")
def test_product_zoom_spans_requested_duration(tmp_path: Path) -> None:
    from demo_studio.looks import _ffprobe_duration

    src = tmp_path / "picture.mp4"
    out = tmp_path / "zoomed.mp4"
    proc = subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=0x224466:s=640x360:d=1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(src),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr[-500:]
    # Short source, long target — must not just bake 1s of zoom.
    apply_look(src, out, look="product-zoom", duration_s=3.0)
    assert out.is_file() and out.stat().st_size > 0
    dur = _ffprobe_duration(out)
    assert dur >= 2.5
