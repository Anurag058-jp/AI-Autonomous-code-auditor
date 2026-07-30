def test_dashboard_module_imports():
    from auditor.dashboard import main

    assert callable(main)
