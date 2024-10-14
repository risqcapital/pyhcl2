from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Never, Self, MutableMapping, MutableSequence, overload, Iterable

from dataclasses import dataclass, field
from rich.console import Console, ConsoleOptions, ConsoleRenderable, RenderResult
from rich.segment import Segment

import pyhcl2.nodes
from pyhcl2.pymiette import SourceSpan, Diagnostic, LabeledSpan
from pyhcl2.rich_utils import STYLE_KEYWORDS, STYLE_NUMBER, STYLE_STRING, Inline, STYLE_PROPERTY_NAME


@dataclass(kw_only=True, frozen=True)
class Value(ConsoleRenderable):
    span: SourceSpan | None = None

    def with_span(self, span: SourceSpan) -> Self:
        return dataclasses.replace(self, span=span)

    @staticmethod
    def infer(value: object) -> "Value":
        match value:
            case None: return Null()
            case int() as value: return Integer(value)
            case float() as value: return Float(value)
            case str() as value: return String(value)
            case bool() as value: return Boolean(value)
            case Sequence() as value: return Array([Value.infer(item) for item in value])
            case Mapping() as value: return Object({String(str(k)): Value.infer(v) for k, v in value.items()})
            case Value() as value: return value
            case _: raise NotImplementedError()

    def resolve(self) -> "Value":
        return self

    def raise_on_unknown(self) -> "Value":
        return self

    def raw(self) -> object: ...

    @property
    def type_name(self) -> str:
        return type(self).__name__.lower()

    def __not_equals__(self, other: "Value") -> "Boolean":
        try:
            return Boolean(
                not (
                    getattr(self, "__equals__")(other).raw()
                )
            )
        except AttributeError:
            return Boolean(True)

@dataclass(eq=True, frozen=True)
class Null(Value):
    def raw(self) -> None:
        return None

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Segment("null", style=STYLE_KEYWORDS)

@dataclass(eq=True, frozen=True)
class Integer(Value):
    _raw: int
    
    def raw(self) -> int:
        return self._raw

    def __add__(self, other: Value) -> Value:
        match other:
            case Integer() as other: return Integer(self._raw + other.raw())
            case Float() as other: return Float(self._raw + other.raw())
            case _: raise NotImplementedError()

    def __sub__(self, other: Value) -> Value:
        match other:
            case Integer() as other: return Integer(self._raw - other.raw())
            case Float() as other: return Float(self._raw - other.raw())
            case _: raise NotImplementedError()

    def __mul__(self, other: Value) -> Value:
        match other:
            case Integer() as other: return Integer(self._raw * other.raw())
            case Float() as other: return Float(self._raw * other.raw())
            case _: raise NotImplementedError()

    def __truediv__(self, other: Value) -> Value:
        match other:
            case Integer() as other: return Float(self._raw / other.raw())
            case Float() as other: return Float(self._raw / other.raw())
            case _: raise NotImplementedError()

    def __mod__(self, other: Value) -> Value:
        match other:
            case Integer() as other: return Integer(self._raw % other.raw())
            case Float() as other: return Float(self._raw % other.raw())
            case _: raise NotImplementedError()

    def __equals__(self, other: Value) -> "Boolean":
        match other:
            case Integer() as other: return Boolean(self._raw == other.raw())
            case Float() as other: return Boolean(self._raw == other.raw())
            case _: return Boolean(False)

    def __lt__(self, other: Value) -> "Boolean":
        match other:
            case Integer() as other: return Boolean(self._raw < other.raw())
            case Float() as other: return Boolean(self._raw < other.raw())
            case _: raise NotImplementedError()

    def __gt__(self, other: Value) -> "Boolean":
        match other:
            case Integer() as other: return Boolean(self._raw > other.raw())
            case Float() as other: return Boolean(self._raw > other.raw())
            case _: raise NotImplementedError()

    def __le__(self, other: Value) -> "Boolean":
        match other:
            case Integer() as other: return Boolean(self._raw <= other.raw())
            case Float() as other: return Boolean(self._raw <= other.raw())
            case _: raise NotImplementedError()

    def __ge__(self, other: Value) -> "Boolean":
        match other:
            case Integer() as other: return Boolean(self._raw >= other.raw())
            case Float() as other: return Boolean(self._raw >= other.raw())
            case _: raise NotImplementedError()

    def __neg__(self):
        return Integer(-self._raw)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Segment(str(self._raw), style=STYLE_NUMBER)

@dataclass(eq=True, frozen=True)
class String(Value):
    _raw: str

    def raw(self) -> str:
        return self._raw

    def __add__(self, other: Value) -> Value:
        match other:
            case String() as other: return String(self._raw + other.raw())
            case _: raise NotImplementedError()

    def __mul__(self, other: Value) -> Value:
        match other:
            case Integer() as other: return String(self._raw * other.raw())
            case _: raise NotImplementedError()

    def __equals__(self, other: Value) -> "Boolean":
        match other:
            case String() as other: return Boolean(self._raw == other.raw())
            case _: return Boolean(False)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Segment(repr(self._raw), style=STYLE_STRING)

@dataclass(eq=True, frozen=True)
class Float(Value):
    _raw: float

    def raw(self) -> float:
        return self._raw

    def __add__(self, other: Value) -> Value:
        match other:
            case Integer() as other: return Float(self._raw + other.raw())
            case Float() as other: return Float(self._raw + other.raw())
            case _: raise NotImplementedError()

    def __sub__(self, other: Value) -> Value:
        match other:
            case Integer() as other: return Float(self._raw - other.raw())
            case Float() as other: return Float(self._raw - other.raw())
            case _: raise NotImplementedError()

    def __mul__(self, other: Value) -> Value:
        match other:
            case Integer() as other: return Float(self._raw * other.raw())
            case Float() as other: return Float(self._raw * other.raw())
            case _: raise NotImplementedError()

    def __truediv__(self, other: Value) -> Value:
        match other:
            case Integer() as other: return Float(self._raw / other.raw())
            case Float() as other: return Float(self._raw / other.raw())
            case _: raise NotImplementedError()

    def __mod__(self, other: Value) -> Value:
        match other:
            case Integer() as other: return Float(self._raw % other.raw())
            case Float() as other: return Float(self._raw % other.raw())
            case _: raise NotImplementedError()

    def __equals__(self, other: Value) -> "Boolean":
        match other:
            case Integer() as other: return Boolean(self._raw == other.raw())
            case Float() as other: return Boolean(self._raw == other.raw())
            case _: return Boolean(False)

    def __lt__(self, other: Value) -> "Boolean":
        match other:
            case Integer() as other: return Boolean(self._raw < other.raw())
            case Float() as other: return Boolean(self._raw < other.raw())
            case _: raise NotImplementedError()

    def __gt__(self, other: Value) -> "Boolean":
        match other:
            case Integer() as other: return Boolean(self._raw > other.raw())
            case Float() as other: return Boolean(self._raw > other.raw())
            case _: raise NotImplementedError()

    def __le__(self, other: Value) -> "Boolean":
        match other:
            case Integer() as other: return Boolean(self._raw <= other.raw())
            case Float() as other: return Boolean(self._raw <= other.raw())
            case _: raise NotImplementedError()

    def __ge__(self, other: Value) -> "Boolean":
        match other:
            case Integer() as other: return Boolean(self._raw >= other.raw())
            case Float() as other: return Boolean(self._raw >= other.raw())
            case _: raise NotImplementedError()

    def __neg__(self):
        return Float(-self._raw)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Segment(str(self._raw), style=STYLE_NUMBER)

@dataclass(eq=True, frozen=True)
class Boolean(Value):
    _raw: bool

    def raw(self) -> bool:
        return self._raw

    def __and__(self, other: Value) -> "Boolean":
        match other:
            case Boolean() as other: return Boolean(self._raw and other.raw())
            case _: raise NotImplementedError()

    def __or__(self, other):
        match other:
            case Boolean() as other: return Boolean(self._raw or other.raw())
            case _: raise NotImplementedError()

    def __not__(self):
        return Boolean(not self._raw)

    def __equals__(self, other: Value) -> "Boolean":
        match other:
            case Boolean() as other: return Boolean(self._raw == other.raw())
            case _: return Boolean(False)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Segment(str(self._raw).lower(), style=STYLE_KEYWORDS)

@dataclass(eq=True, frozen=True)
class Array(Value, MutableSequence[Value]):
    _raw: list[Value]

    def insert(self, index, value):
        self._raw.insert(index, value)

    @overload
    def __getitem__(self, index: int) -> Value: ...

    @overload
    def __getitem__(self, index: slice) -> MutableSequence[Value]: ...

    def __getitem__(self, index):
        return self._raw[index]

    @overload
    def __setitem__(self, index: int, value: Value) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[Value]) -> None: ...

    def __setitem__(self, index, value):
        self._raw[index] = value

    @overload
    def __delitem__(self, index: int) -> None: ...

    @overload
    def __delitem__(self, index: slice) -> None: ...

    def __delitem__(self, index):
        del self._raw[index]

    def __len__(self):
        return len(self._raw)

    def raw(self) -> list[object]:
        return [item.raw() for item in self._raw]

    def resolve(self) -> "Value":
        unknown = []
        for item in self._raw:
            if isinstance(item, Unknown):
                unknown.append(item)
        if unknown:
            return Unknown.indirect(*unknown)
        return self

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Segment("[")
        for i, item in enumerate(self._raw):
            yield item
            if i < len(self._raw) - 1:
                yield Segment(", ")

        yield Segment("]")

@dataclass(eq=True, frozen=True)
class Object(Value, MutableMapping[String, Value]):
    _raw: dict[String, Value]

    def __setitem__(self, key, value):
        self._raw[key] = value

    def __getitem__(self, key):
        return self._raw[key]

    def __delitem__(self, key):
        del self._raw[key]

    def __len__(self):
        return len(self._raw)

    def __iter__(self):
        return iter(self._raw)

    def raw(self) -> dict[object, object]:
        return {key.raw(): value.raw() for key, value in self._raw.items()}

    def resolve(self) -> "Value":
        unknown = []
        for key, value in self._raw.items():
            if isinstance(key, Unknown):
                unknown.append(key)
        if unknown:
            return Unknown.indirect(*unknown)
        return self

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Segment("{")
        for i, (key, value) in enumerate(self._raw.items()):
            yield Segment(key.raw(), style=STYLE_PROPERTY_NAME)
            yield Segment(" = ")
            yield value
            if i < len(self._raw) - 1:
                yield Segment(", ")

        yield Segment("}")

@dataclass(eq=True, frozen=True)
class VariableReference:
    key: tuple[str | None, ...]
    span: SourceSpan

@dataclass(eq=True, frozen=True)
class Unknown(Value):
    # TODO: Write docs on what direct and indirect references are
    direct_references: set[VariableReference] = field(default_factory=set)
    indirect_references: set[VariableReference] = field(default_factory=set)

    def raise_on_unknown(self) -> Never:
        raise Diagnostic(
            code="pyhcl2::evaluator::unknown_variable",
            message=Inline("Failed to evaluate expression due to unknown variables"),
            labels=[LabeledSpan(ref.span, f"{ref.key[-1]} could not be resolved ({".".join([k if k else "?" for k in ref.key])})") for ref in self.references],
        )

    def raw(self) -> Never:
        self.raise_on_unknown()

    @property
    def references(self) -> set[VariableReference]:
        return self.direct_references | self.indirect_references

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Segment("<")
        yield Segment("Unknown due to missing variables, direct: ", style=STYLE_KEYWORDS)
        for i, ref in enumerate(self.direct_references):
            for j, key in enumerate(ref.key):
                yield Segment(key if key else "?")
                if j < len(ref.key) - 1:
                    yield Segment(".")
            if i < len(self.direct_references) - 1:
                yield Segment(", ")
        yield Segment(", indirect: ", style=STYLE_KEYWORDS)
        for i, ref in enumerate(self.indirect_references):
            for j, key in enumerate(ref.key):
                yield Segment(key if key else "?")
                if j < len(ref.key) - 1:
                    yield Segment(".")
            if i < len(self.indirect_references) - 1:
                yield Segment(", ")
        yield Segment(f">")

    @staticmethod
    def indirect(*values: Value) -> Unknown:
        return Unknown(
            set(),
            set([ref for value in values if isinstance(value, Unknown) for ref in value.references]),
        )

    def direct(self, span: SourceSpan, key: str) -> "Unknown":
        if self.direct_references:
            direct_refs = set([VariableReference((*ref.key, key,), span) for ref in self.direct_references])
        else:
            direct_refs = {VariableReference((None, key,), span)}

        return Unknown(direct_refs, self.references)

    @staticmethod
    def ident(identifier: "pyhcl2.nodes.Identifier") -> Unknown:
        return Unknown(
            {VariableReference((identifier.name,), identifier.span)},
            set(),
        )
