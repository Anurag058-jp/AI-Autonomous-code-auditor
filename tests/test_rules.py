from auditor.rules import run_rules


def test_finds_hardcoded_secret():
    findings = run_rules("config.py", 'API_KEY = "a-very-long-secret"')
    assert findings[0].rule_id == "SEC001"
    assert findings[0].file_path == "config.py"


def test_finds_unsafe_pickle():
    assert any(f.rule_id == "SEC003" for f in run_rules("x.py", "pickle.loads(payload)"))

