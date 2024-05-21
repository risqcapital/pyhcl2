from pathlib import Path

import pyhcl2
import pytest
from pyhcl2 import parse_module

testcases_dir = Path(__file__).parent / "testcases"


@pytest.mark.parametrize("filename", list(testcases_dir.iterdir()))
def test_testcase(filename: Path) -> None:
    content = filename.read_text()
    hcl2_code, expected_pformat = content.split("===")[1:]
    assert parse_module(hcl2_code) == eval(
        expected_pformat.strip(),
        {k: getattr(pyhcl2, k) for k in pyhcl2.__all__},
    )
