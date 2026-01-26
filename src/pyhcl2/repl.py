# ruff: noqa: PLC0415
from pathlib import Path

import rich
from pyagnostics.exceptions import DiagnosticError
from pyagnostics.source import InMemorySource, attach_diagnostic_source_code
from pyagnostics.spans import SourceId
from rich.console import NewLine

from pyhcl2.eval import EvaluationScope, Evaluator
from pyhcl2.parse import parse_expr_or_stmt
from pyhcl2.rich_utils import HclHighlighter, Inline


def main() -> None:
    from prompt_toolkit import PromptSession  # type: ignore
    from prompt_toolkit.auto_suggest import AutoSuggestFromHistory  # type: ignore
    from prompt_toolkit.history import FileHistory  # type: ignore

    scope = EvaluationScope()
    evaluator = Evaluator(intrinsic_functions={"identity": lambda x: x})
    session: PromptSession = PromptSession(
        history=FileHistory(Path.home() / ".pyhcl2_history")
    )
    try:
        while True:
            text = session.prompt("> ", auto_suggest=AutoSuggestFromHistory())

            if text == "":
                continue

            if text == "exit":
                break

            src = InMemorySource(text)
            source_id = SourceId()
            try:
                with attach_diagnostic_source_code(src, source_id=source_id):
                    ast = parse_expr_or_stmt(text, source_id=source_id)
                with attach_diagnostic_source_code(
                    src, highlighter=HclHighlighter(ast), source_id=source_id
                ):
                    result = evaluator.eval(ast, scope)
                    rich.print(Inline(result.resolve().raise_on_unknown(), NewLine()))
            except DiagnosticError as diagnostic:
                rich.get_console().print(diagnostic, highlight=False)

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
