import pycodestyle


def test_conformance():
    """Test that we conform to PEP-8."""
    style = pycodestyle.StyleGuide(quiet=False, ignore=['E501', 'E241'])
    style.input_dir('httpie')
    style.input_dir('tests')
    result = style.check_files()
    assert result.total_errors == 0
