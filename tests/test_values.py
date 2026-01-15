from pathlib import Path

import pytest

from pyhcl2.values import Array, Boolean, Float, Integer, Null, Object, String, Value


def test_value_infer_bool() -> None:
    assert Value.infer(True) == Boolean(True)
    assert Value.infer(False) == Boolean(False)


def test_value_infer_int() -> None:
    assert Value.infer(1) == Integer(1)


def test_value_infer_float() -> None:
    assert Value.infer(1.5) == Float(1.5)


def test_value_infer_string() -> None:
    assert Value.infer("hello") == String("hello")


def test_value_infer_null() -> None:
    assert Value.infer(None) == Null()


def test_value_infer_sequence() -> None:
    assert Value.infer([1, "a"]) == Array([Integer(1), String("a")])


def test_value_infer_mapping() -> None:
    assert Value.infer({"a": 1}) == Object({String("a"): Integer(1)})


def test_value_infer_passthrough() -> None:
    value = Integer(42)
    assert Value.infer(value) is value


def test_value_infer_pathlike() -> None:
    assert Value.infer(Path("/tmp/example")) == String("/tmp/example")


def test_value_infer_unknown_type() -> None:
    with pytest.raises(NotImplementedError):
        Value.infer(object())
