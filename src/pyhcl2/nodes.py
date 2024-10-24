from __future__ import annotations

import dataclasses
import typing as t
from collections.abc import Iterable
from dataclasses import dataclass, field
from functools import cached_property

from pyagnostics.spans import SourceSpan
from rich.console import (
    Console,
    ConsoleOptions,
    ConsoleRenderable,
    RenderResult,
)
from rich.padding import Padding
from rich.segment import Segment
from rich.text import Span

from pyhcl2.rich_utils import (
    STYLE_FUNCTION,
    STYLE_KEYWORDS,
    STYLE_PROPERTY_NAME,
)
from pyhcl2.values import String, Value


@dataclass(frozen=True, eq=True, kw_only=True)
class Node(ConsoleRenderable):
    """Base class for HCL2 AST nodes."""

    span: SourceSpan = field(default=SourceSpan(-1, -1), compare=False, hash=False)

    def rich_highlights(self) -> Iterable[Span]:
        return []


class Expression(Node):
    """Base class for nodes that represent expressions in HCL2."""


@dataclass(frozen=True, eq=True)
class Literal(Expression):
    value: Value

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield self.value

    def rich_highlights(self) -> Iterable[Span]:
        return self.value.rich_highlights()


@dataclass(frozen=True, eq=True)
class ArrayExpression(Expression):
    values: list[Expression]

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Segment("[")
        for i, value in enumerate(self.values):
            yield value
            if i < len(self.values) - 1:
                yield Segment(", ")
        yield Segment("]")

    def rich_highlights(self) -> Iterable[Span]:
        for value in self.values:
            yield from value.rich_highlights()


@dataclass(frozen=True, eq=True)
class ObjectExpression(Expression):
    fields: dict[Expression, Expression]

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Segment("{")
        for i, (key, value) in enumerate(self.fields.items()):
            if isinstance(key, Identifier):
                yield Segment(key.name, style=STYLE_PROPERTY_NAME)
            else:
                yield key
            yield Segment(" = ")
            yield value
            if i < len(self.fields) - 1:
                yield Segment(", ")
        yield Segment("}")

    def rich_highlights(self) -> Iterable[Span]:
        for key, value in self.fields.items():
            if isinstance(key, Identifier):
                yield key.span.styled(STYLE_PROPERTY_NAME)
            else:
                yield from key.rich_highlights()
            yield from value.rich_highlights()


@dataclass(frozen=True, eq=True)
class Identifier(Expression):
    name: str

    def as_string(self) -> String:
        return String(
            self.name,
            span=self.span,
        )

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Segment(self.name)

    def rich_highlights(self) -> Iterable[Span]:
        return []


@dataclass(frozen=True, eq=True)
class FunctionCall(Expression):
    ident: Identifier
    args: list[Expression]
    var_args: bool = False

    @property
    def args_span(self) -> SourceSpan:
        return SourceSpan(self.ident.span.end, self.span.end)

    def __post_init__(self) -> None:
        assert all(isinstance(arg, Expression) for arg in self.args), self.args

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Segment(self.ident.name, style=STYLE_FUNCTION)
        yield Segment("(")
        for i, arg in enumerate(self.args):
            yield arg
            if i < len(self.args) - 1:
                yield Segment(", ")
        if self.var_args:
            yield Segment("...")
        yield Segment(")")

    def rich_highlights(self) -> Iterable[Span]:
        yield self.ident.span.styled(STYLE_FUNCTION)
        for arg in self.args:
            yield from arg.rich_highlights()


@dataclass(frozen=True, eq=True)
class GetAttrKey(Node):
    ident: Identifier

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Segment(".")
        yield self.ident


@dataclass(frozen=True, eq=True)
class GetIndexKey(Node):
    expr: Expression

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Segment("[")
        yield self.expr
        yield Segment("]")

    def rich_highlights(self) -> Iterable[Span]:
        yield from self.expr.rich_highlights()


@dataclass(frozen=True, eq=True)
class GetAttr(Expression):
    on: Expression
    key: GetAttrKey

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield self.on
        yield self.key

    def rich_highlights(self) -> Iterable[Span]:
        yield from self.on.rich_highlights()
        yield from self.key.ident.rich_highlights()


@dataclass(frozen=True, eq=True)
class GetIndex(Expression):
    on: Expression
    key: GetIndexKey

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield self.on
        yield self.key

    def rich_highlights(self) -> Iterable[Span]:
        yield from self.on.rich_highlights()
        yield from self.key.expr.rich_highlights()


@dataclass(frozen=True, eq=True)
class AttrSplat(Expression):
    on: Expression
    keys: list[GetAttrKey] = dataclasses.field(default_factory=list)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield self.on
        yield Segment(".*")
        yield from self.keys

    def rich_highlights(self) -> Iterable[Span]:
        yield from self.on.rich_highlights()
        for key in self.keys:
            yield from key.ident.rich_highlights()


@dataclass(frozen=True, eq=True)
class IndexSplat(Expression):
    on: Expression
    keys: list[GetAttrKey | GetIndexKey] = dataclasses.field(default_factory=list)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield self.on
        yield Segment("[*]")
        yield from self.keys

    def rich_highlights(self) -> Iterable[Span]:
        yield from self.on.rich_highlights()
        for key in self.keys:
            yield from key.rich_highlights()


@dataclass(frozen=True, eq=True)
class UnaryOperator(Node):
    type: t.Literal["-", "!"]

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Segment(self.type)

    def rich_highlights(self) -> Iterable[Span]:
        return []


@dataclass(frozen=True, eq=True)
class UnaryExpression(Expression):
    op: UnaryOperator
    expr: Expression

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield self.op
        yield self.expr

    def rich_highlights(self) -> Iterable[Span]:
        yield from self.op.rich_highlights()
        yield from self.expr.rich_highlights()


@dataclass(frozen=True, eq=True)
class BinaryOperator(Node):
    type: t.Literal[
        "==", "!=", "<", ">", "<=", ">=", "-", "*", "/", "%", "&&", "||", "+"
    ]

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Segment(self.type)

    def rich_highlights(self) -> Iterable[Span]:
        return []


@dataclass(frozen=True, eq=True)
class BinaryExpression(Expression):
    op: BinaryOperator
    left: Expression
    right: Expression

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield self.left
        yield Segment(" ")
        yield self.op
        yield Segment(" ")
        yield self.right

    def rich_highlights(self) -> Iterable[Span]:
        yield from self.left.rich_highlights()
        yield from self.op.rich_highlights()
        yield from self.right.rich_highlights()


@dataclass(frozen=True, eq=True)
class Conditional(Expression):
    cond: Expression
    then_expr: Expression
    else_expr: Expression

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield self.cond
        yield Segment(" ? ")
        yield self.then_expr
        yield Segment(" : ")
        yield self.else_expr

    def rich_highlights(self) -> Iterable[Span]:
        yield from self.cond.rich_highlights()
        yield from self.then_expr.rich_highlights()
        yield from self.else_expr.rich_highlights()


@dataclass(frozen=True, eq=True)
class Parenthesis(Expression):
    expr: Expression

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Segment("(")
        yield self.expr
        yield Segment(")")

    def rich_highlights(self) -> Iterable[Span]:
        yield from self.expr.rich_highlights()


@dataclass(frozen=True, eq=True)
class ForTupleExpression(Expression):
    key_ident: Identifier | None
    value_ident: Identifier
    collection: Expression
    value: Expression
    condition: Expression | None

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Segment("[")
        yield Segment("for ", style=STYLE_KEYWORDS)
        if self.key_ident is not None:
            yield self.key_ident
            yield Segment(", ")
        yield self.value_ident
        yield Segment(" in ", style=STYLE_KEYWORDS)
        yield self.collection
        yield Segment(" : ")
        yield self.value
        if self.condition is not None:
            yield Segment(" if ", style=STYLE_KEYWORDS)
            yield self.condition
        yield Segment("]")

    def rich_highlights(self) -> Iterable[Span]:
        yield SourceSpan(
            self.span.start + 1,
            self.key_ident.span.start - 1
            if self.key_ident is not None
            else self.value_ident.span.start - 1,
        ).styled(STYLE_KEYWORDS)

        if self.key_ident is not None:
            yield from self.key_ident.rich_highlights()
        yield from self.value_ident.rich_highlights()

        yield SourceSpan(
            self.value_ident.span.end + 1, self.collection.span.start - 1
        ).styled(STYLE_KEYWORDS)

        yield from self.collection.rich_highlights()
        yield from self.value.rich_highlights()
        if self.condition is not None:
            yield SourceSpan(
                self.value.span.end + 1, self.condition.span.start - 1
            ).styled(STYLE_KEYWORDS)
            yield from self.condition.rich_highlights()


@dataclass(frozen=True, eq=True)
class ForObjectExpression(Expression):
    key_ident: Identifier | None
    value_ident: Identifier
    collection: Expression
    key: Expression
    value: Expression
    condition: Expression | None
    grouping_mode: bool = dataclasses.field(default=False)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Segment("{")
        yield Segment("for ", style=STYLE_KEYWORDS)
        if self.key_ident is not None:
            yield self.key_ident
            yield Segment(", ")
        yield self.value_ident
        yield Segment(" in ", style=STYLE_KEYWORDS)
        yield self.collection
        yield Segment(" : ")
        yield self.key
        yield Segment(" => ")
        yield self.value
        if self.condition is not None:
            yield Segment(" if ", style=STYLE_KEYWORDS)
            yield self.condition
        if self.grouping_mode:
            yield Segment("...")
        yield Segment("}")

    def rich_highlights(self) -> Iterable[Span]:
        yield SourceSpan(
            self.span.start + 1,
            self.key_ident.span.start - 1
            if self.key_ident is not None
            else self.value_ident.span.start - 1,
        ).styled(STYLE_KEYWORDS)
        yield from (
            self.key_ident.rich_highlights() if self.key_ident is not None else []
        )
        yield from self.value_ident.rich_highlights()
        yield SourceSpan(
            self.value_ident.span.end + 1, self.collection.span.start - 1
        ).styled(STYLE_KEYWORDS)
        yield from self.collection.rich_highlights()
        yield from self.key.rich_highlights()
        if self.condition is not None:
            yield SourceSpan(
                self.value.span.end + 1, self.condition.span.start - 1
            ).styled(STYLE_KEYWORDS)
            yield from self.condition.rich_highlights()


class Stmt(Node):
    """Base class for nodes that represent statements in HCL2."""

    @property
    def key_path(self) -> tuple[str, ...]:
        raise NotImplementedError()


@dataclass(frozen=True, eq=True)
class Attribute(Stmt):
    key: Identifier
    value: Expression

    @property
    def key_path(self) -> tuple[str, ...]:
        return (self.key.name,)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Segment(self.key.name, style=STYLE_PROPERTY_NAME)
        yield Segment(" = ")
        yield self.value

    def rich_highlights(self) -> Iterable[Span]:
        yield self.key.span.styled(STYLE_PROPERTY_NAME)
        yield from self.value.rich_highlights()


@dataclass(frozen=True, eq=True)
class Block(Stmt):
    type: Identifier
    labels: list[Literal | Identifier]
    body: list[Stmt]

    @property
    def keys(self) -> tuple[String, ...]:
        key_parts: list[String] = [self.type.as_string()]
        for label in self.labels:
            match label:
                case Identifier() as label:
                    key_parts.append(label.as_string())
                case Literal(value=String() as string):
                    key_parts.append(string)
                case _:
                    pass
        return tuple(key_parts)

    @property
    def key_path(self) -> tuple[str, ...]:
        key_parts: list[str] = [self.type.name]
        for label in self.labels:
            if isinstance(label, Identifier):
                key_parts.append(label.name)
            elif isinstance(label, Literal) and isinstance(label.value, String):
                key_parts.append(label.value.raw())
        return tuple(key_parts)

    def key(self) -> tuple[str, ...]:
        return self.key_path

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Segment(self.type.name, style=STYLE_KEYWORDS)
        for label in self.labels:
            yield Segment(" ")
            yield label
        yield Segment(" {")
        yield Segment("\n")
        for stmt in self.body:
            yield Padding(stmt, (0, 2))
        yield Segment("}")

    def rich_highlights(self) -> Iterable[Span]:
        yield self.type.span.styled(STYLE_KEYWORDS)
        for label in self.labels:
            yield from label.rich_highlights()
        for stmt in self.body:
            yield from stmt.rich_highlights()

    @cached_property
    def attributes(self) -> dict[str, Expression]:
        return {
            stmt.key.name: stmt.value
            for stmt in self.body
            if isinstance(stmt, Attribute)
        }

    @cached_property
    def blocks(self) -> list[Block]:
        return [stmt for stmt in self.body if isinstance(stmt, Block)]


@dataclass(frozen=True, eq=True)
class Module(Node):
    body: list[Stmt]

    def get_blocks(self, block_type: str | None) -> list[Block]:
        return [
            stmt
            for stmt in self.body
            if isinstance(stmt, Block)
            and (block_type is None or stmt.type.name == block_type)
        ]

    def get_block(self, block_type: str, *labels: str) -> Block | None:
        blocks = self.get_blocks(block_type)

        if len(labels) > 0:
            blocks = [
                block
                for block in blocks
                if block.labels == [Literal(String(label)) for label in labels]
            ]

        if len(blocks) > 1:
            raise ValueError(f"Multiple {block_type} blocks found")
        if len(blocks) == 0:
            return None
        return blocks[0]

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        for stmt in self.body:
            yield stmt
            yield Segment("\n")

    def rich_highlights(self) -> Iterable[Span]:
        for stmt in self.body:
            yield from stmt.rich_highlights()


class VarArgsMarker(Node):
    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Segment("...")
