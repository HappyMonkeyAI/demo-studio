from demo_studio.neo_script import compile_neo_run_js


def test_compile_contains_beats():
    data = {
        "product": "t",
        "beats": [
            {
                "id": "home",
                "narration": "hi",
                "actions": [{"type": "navigate", "path": "/"}],
                "assert": [{"type": "http_ok", "path": "/"}],
            }
        ],
    }
    js = compile_neo_run_js(data, base_url="http://127.0.0.1:9999")
    assert "beat: 'home'" in js or 'beat: "home"' in js
    assert "browser.open" in js
    assert "page.goto" in js
