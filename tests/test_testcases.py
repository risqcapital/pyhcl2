from pathlib import Path

import pytest
from pyhcl2.parse import parse_string

testcases_dir = Path(__file__).parent / "testcases"


@pytest.mark.parametrize("filename", list(testcases_dir.iterdir()))
def test_testcase(filename: Path) -> None:
    content = filename.read_text()
    hcl2_code, expected_pformat = content.split("===")[1:]
    module = parse_string(hcl2_code)
    assert module.pformat(False).strip() == expected_pformat.strip()
