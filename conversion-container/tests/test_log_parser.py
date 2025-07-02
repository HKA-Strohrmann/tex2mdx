import pytest
from conversion.services.latexml import list_missing_packages


@pytest.mark.logparser_unit_tests
def test_find_package_and_class():
    latexml_log = """
Warning:missing_file:imsart Can't find binding for class imsart (using OmniBus)
Warning:missing_file:xifthen Can't find package xifthen
Warning:missing_file: fail.
Warning:missing_file:biblatex.sty biblatex.sty is only minimally stubbed and will not be interpreted raw.
Info:fallback:revtex4-2.cls Interpreted 4-2 as a versioned package/class name, falling back to generic revtex.cls
"""
    missing_packages = list_missing_packages(latexml_log)
    assert missing_packages == [
        "imsart.cls",
        "xifthen.sty",
        "biblatex.sty",
    ], "Failed to correctly extract missing package/class name"
