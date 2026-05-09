import eventflow


def test_eventflow_package_imports() -> None:
    assert isinstance(eventflow.__version__, str)
    assert eventflow.__version__
