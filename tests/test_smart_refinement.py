"""Test that smart_refinement module loads without syntax errors."""


def test_module_imports():
    """The critical syntax error fix — ensure the module loads."""
    import council.smart_refinement  # noqa: F401
