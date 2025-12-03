def test_basic():
    """Basic test to ensure testing works"""
    assert True

def test_import_app():
    """Test that app can be imported"""
    try:
        import app
        assert True
    except ImportError:
        assert False, "Could not import app"
