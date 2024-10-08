from __future__ import annotations

import dataclasses
import typing as t
from dataclasses import dataclass
from functools import cached_property

LiteralValue = None | bool | int | float | str


@dataclass(frozen=True, eq=True, kw_only=True)
class Node:
    """Base class for HCL2 AST nodes."""

    start_pos: int | None = None
    end_pos: int | None = None


class Expression(Node):
    """Base class for nodes that represent expressions in HCL2."""


@dataclass(frozen=True, eq=True)
class Literal(Expression):
    value: LiteralValue

    def __post_init__(self) -> None:
        assert isinstance(self.value, (type(None), bool, int, float, str)), self.value


@dataclass(frozen=True, eq=True)
class Array(Expression):
    values: list[Expression]


@dataclass(frozen=True, eq=True)
class Object(Expression):
    fields: dict[Expression, Expression]


@dataclass(frozen=True, eq=True)
class Identifier(Expression):
    name: str


@dataclass(frozen=True, eq=True)
class FunctionCall(Expression):
    ident: Identifier
    args: list[Expression]
    var_args: bool = False

    def __post_init__(self) -> None:
        assert all(isinstance(arg, Expression) for arg in self.args), self.args


@dataclass(frozen=True, eq=True)
class GetAttrKey(Node):
    ident: Identifier


@dataclass(frozen=True, eq=True)
class GetIndexKey(Node):
    expr: Expression


@dataclass(frozen=True, eq=True)
class GetAttr(Expression):
    on: Expression
    key: GetAttrKey


@dataclass(frozen=True, eq=True)
class GetIndex(Expression):
    on: Expression
    key: GetIndexKey


@dataclass(frozen=True, eq=True)
class AttrSplat(Expression):
    on: Expression
    keys: list[GetAttrKey] = dataclasses.field(default_factory=list)


@dataclass(frozen=True, eq=True)
class IndexSplat(Expression):
    on: Expression
    keys: list[GetAttrKey | GetIndexKey] = dataclasses.field(default_factory=list)


@dataclass(frozen=True, eq=True)
class UnaryOperator(Node):
    type: t.Literal["-", "!"]


@dataclass(frozen=True, eq=True)
class UnaryExpression(Expression):
    op: UnaryOperator
    expr: Expression


@dataclass(frozen=True, eq=True)
class BinaryOperator(Node):
    type: t.Literal[
        "==", "!=", "<", ">", "<=", ">=", "-", "*", "/", "%", "&&", "||", "+"
    ]


@dataclass(frozen=True, eq=True)
class BinaryExpression(Expression):
    op: BinaryOperator
    left: Expression
    right: Expression


@dataclass(frozen=True, eq=True)
class Conditional(Expression):
    cond: Expression
    then_expr: Expression
    else_expr: Expression


@dataclass(frozen=True, eq=True)
class Parenthesis(Expression):
    expr: Expression


@dataclass(frozen=True, eq=True)
class ForTupleExpression(Expression):
    key_ident: Identifier | None
    value_ident: Identifier
    collection: Expression
    value: Expression
    condition: Expression | None


@dataclass(frozen=True, eq=True)
class ForObjectExpression(Expression):
    key_ident: Identifier | None
    value_ident: Identifier
    collection: Expression
    key: Expression
    value: Expression
    condition: Expression | None
    grouping_mode: bool = dataclasses.field(default=False)


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


@dataclass(frozen=True, eq=True)
class Block(Stmt):
    type: Identifier
    labels: list[Literal | Identifier]
    body: list[Stmt]

    @property
    def key_path(self) -> tuple[str, ...]:
        key_parts: list[str] = [self.type.name]
        for label in self.labels:
            if isinstance(label, Identifier):
                key_parts.append(label.name)
            elif isinstance(label, Literal) and isinstance(label.value, str):
                key_parts.append(label.value)
        return tuple(key_parts)

    def key(self) -> tuple[str, ...]:
        return self.key_path

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
            and (block_type is None or stmt.type == block_type)
        ]

    def get_block(self, block_type: str, *labels: str) -> Block | None:
        blocks = self.get_blocks(block_type)

        if len(labels) > 0:
            blocks = [
                block
                for block in blocks
                if block.labels == [Literal(label) for label in labels]
            ]

        if len(blocks) > 1:
            raise ValueError(f"Multiple {block_type} blocks found")
        if len(blocks) == 0:
            return None
        return blocks[0]
