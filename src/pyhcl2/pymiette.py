from enum import StrEnum, auto
from typing import Union, Callable

import rich
from dataclasses import dataclass, field
from rich.abc import RichRenderable
from rich.color import Color
from rich.console import Console, ConsoleOptions, Group, RenderResult, RichCast, ConsoleRenderable, NewLine, \
    RenderableType
from rich.padding import Padding
from rich.segment import Segment
from rich.style import Style
from rich.styled import Styled
from rich.terminal_theme import DIMMED_MONOKAI
from rich.text import Text


class Severity(StrEnum):
    ADVICE = auto()
    WARNING = auto()
    ERROR = auto()

    @property
    def style(self) -> Style:
        match self:
            case Severity.ADVICE:
                return Style(color="blue")
            case Severity.WARNING:
                return Style(color="yellow")
            case Severity.ERROR:
                return Style(color="red")

@dataclass(unsafe_hash=True)
class SourceSpan:
    start_char_index: int
    end_char_index: int

@dataclass
class LabeledSpan:
    span: SourceSpan
    label: RenderableType

    def __post_init__(self):
        if isinstance(self.label, str):
            self.label = Text(self.label, end="")


@dataclass
class LabeledSourceBlock:
    source: str
    title: str | None = None
    start_line: int = 1
    start_char_index: int = 0
    labels: list[LabeledSpan] = field(default_factory=list)

    def __rich_console__(
        self, _console: Console, _options: ConsoleOptions
    ) -> RenderResult:
        if self.title is not None:
            yield Segment(f"  ╭─[{self.title}]\n")
        else:
            yield Segment("  ╭───\n")

        src_line_start_index = self.start_char_index
        for i, line in enumerate(self.source.split("\n")):
            yield Segment(f"{i+self.start_line}", style=Style(dim=True))
            yield Segment(" │ ")
            yield Segment(line)
            yield Segment("\n")

            labels_in_line = [
                label
                for label in self.labels
                if src_line_start_index
                <= label.span.start_char_index
                < src_line_start_index + len(line)
            ]
            labels_in_line = sorted(
                labels_in_line, key=lambda label: label.span.start_char_index
            )

            if labels_in_line:
                for j in range(len(labels_in_line) + 1):
                    yield Segment("  · ")

                    labels_line_length = 0

                    for k, label in enumerate(
                        labels_in_line[: len(labels_in_line) - j + 1]
                    ):
                        before_len = (
                            label.span.start_char_index
                            - src_line_start_index
                            - labels_line_length
                        )
                        label_len = label.span.end_char_index - label.span.start_char_index
                        label_before_middle_len = label_len // 2
                        label_after_middle_len = label_len - label_before_middle_len - 1

                        style = Style(
                            color=Color.from_triplet(DIMMED_MONOKAI.ansi_colors[(k % 7) + 1])
                        )

                        if j == 0:
                            yield Segment(" " * before_len)
                            yield Segment("─" * label_before_middle_len, style)
                            yield Segment("┬", style)
                            yield Segment("─" * label_after_middle_len, style)
                        else:
                            yield Segment(" " * (before_len + label_before_middle_len))
                            if k == len(labels_in_line) - j:
                                yield Segment(f"╰─ ", style)
                                yield Styled(label.label, style)
                            else:
                                yield Segment("│", style)
                                yield Segment(" " * label_after_middle_len)

                        labels_line_length += before_len + label_len

                    yield Segment.line()

            src_line_start_index += len(line) + 1

        yield Segment("  ╰───\n")

@dataclass(kw_only=True)
class Diagnostic(Exception, RichCast):
    severity: Severity = Severity.ERROR
    code: str | None = None
    message: RenderableType
    help: RenderableType | None = None
    source_code: str | None = None
    labels: list[LabeledSpan] = field(default_factory=list)

    def with_context(self, note: str) -> "Diagnostic":
        self.add_note(note)
        return self

    def with_source_code(self, source_code: str) -> "Diagnostic":
        diag = Diagnostic(
            severity=self.severity,
            code=self.code,
            message=self.message,
            help=self.help,
            source_code=source_code,
            labels=self.labels,
        )
        diag.__cause__ = self.__cause__
        diag.__context__ = self.__context__
        diag.__suppress_context__ = self.__suppress_context__
        if hasattr(self, "__notes__"):
           for note in self.__notes__:
               diag.add_note(note)
        diag.__traceback__ = self.__traceback__

        return diag

    def __str__(self):
        return self.message

    def __rich_header(self, _console: Console, _options: ConsoleOptions) -> RenderResult:
        if self.code:
            yield Segment(f"{self.severity.title()}: ", style=self.severity.style)
            yield Segment(self.code, style=self.severity.style)
            yield NewLine()

    def __rich_causes(self, _console: Console, _options: ConsoleOptions) -> RenderResult:
        yield Segment(" × ", style=Style(color="red", bold=True))
        yield self.message

        causes: list[Text] = []

        cause = self.__cause__

        if hasattr(self, "__notes__"):
            for note in self.__notes__:
                causes.append(Text(note))

        while cause:
            causes.append(Text(str(cause).split("\n", 1)[0]))
            cause = cause.__cause__

        for i, c in enumerate(causes):
            if i < len(causes) - 1:
                yield Segment(" ├─▶ ", style=Style(color="red", bold=True))
            else:
                yield Segment(" ╰─▶ ", style=Style(color="red", bold=True))

            yield c

    def __rich_snippets(self, _console: Console, _options: ConsoleOptions) -> RenderResult:
        if self.source_code is None:
            return

        yield NewLine()
        yield LabeledSourceBlock(
            source=self.source_code,
            labels=self.labels,
        )

    def __rich_help(self, _console: Console, _options: ConsoleOptions) -> RenderResult:
        if self.help:
            yield NewLine()
            yield Segment("help: ", style=Style(color="blue"))
            yield self.help



    def __rich__(self) -> Union["ConsoleRenderable", "RichCast", str]:
        @dataclass
        class Wrapped(RichRenderable):
            inner: Callable[[Console, ConsoleOptions], RenderResult]
            def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
                return self.inner(console, options)

        return Padding(
            Group(
                Wrapped(self.__rich_header),
                Padding(
                    Group(
                        Wrapped(self.__rich_causes),
                        Wrapped(self.__rich_snippets),
                        Wrapped(self.__rich_help)
                    ),
                    pad=(0, 1)
                )
            ),
            pad=(1, 1),
        )



if __name__ == "__main__":

    try:
        try:
            test = 1 / 0
        except Exception as e:
            raise Diagnostic(
                severity=Severity.ERROR,
                code="pymiette::basic_diagnostic",
                message="Failed to do things",
                labels=[
                    LabeledSpan(SourceSpan(4, 9), "division by zero"),
                ],
                help="Don't divide by zero",
            ) from e

    except Diagnostic as e:
        rich.print(e)
        rich.print(e.with_source_code("a = 1 / 0"))