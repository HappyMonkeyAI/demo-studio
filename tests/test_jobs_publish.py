import json
from pathlib import Path

from demo_studio.jobs import DemoJobService
from demo_studio.publish import create_publication_draft


def test_create_job_and_list(tmp_path: Path, monkeypatch):
    root = tmp_path
    beats = root / "demo.beats.json"
    beats.write_text(
        json.dumps(
            {
                "version": 1,
                "product": "t",
                "beats": [{"id": "a", "narration": "hello world"}],
            }
        ),
        encoding="utf-8",
    )
    # copy schema expectations: product beats need version 1 — ok
    svc = DemoJobService(root)
    meta = svc.create_job(str(beats), base_url="http://127.0.0.1:9")
    assert meta["job_id"].startswith("job-")
    assert (root / "outputs" / meta["job_id"] / "job.json").is_file()
    assert (root / "outputs" / meta["job_id"] / "neo-run.js").is_file()
    assert svc.list_jobs(5)[0]["job_id"] == meta["job_id"]


def test_publication_draft(tmp_path: Path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "demo.mp4").write_bytes(b"\x00\x00")
    draft = create_publication_draft(run, platform="youtube", title="t")
    assert draft["dry_run"] is True
    assert Path(draft["path"]).is_file()
