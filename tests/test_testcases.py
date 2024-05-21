from pathlib import Path

import pytest
from pyhcl2 import *

testcases_dir = Path(__file__).parent / "testcases"


@pytest.mark.parametrize("filename", list(testcases_dir.iterdir()))
def test_testcase(filename: Path) -> None:
    content = filename.read_text()
    hcl2_code, expected_pformat = content.split("===")[1:]
    assert parse_module(hcl2_code) == eval(expected_pformat.strip())
