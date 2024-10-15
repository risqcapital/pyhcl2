from pathlib import Path

import rich
from prompt_toolkit import PromptSession  # type: ignore
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory  # type: ignore
from prompt_toolkit.history import FileHistory  # type: ignore
from rich.console import NewLine

from pyhcl2.eval import EvaluationScope, Evaluator
from pyhcl2.parse import parse_expr_or_stmt
from pyhcl2.pymiette import DiagnosticError
from pyhcl2.rich_utils import Inline


def main() -> None:
    scope = EvaluationScope()
    evaluator = Evaluator(intrinsic_functions={"test": lambda x: x})
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

            try:
                ast = parse_expr_or_stmt(text)
                result = evaluator.eval(ast, scope)
                rich.print(Inline(result.resolve().raise_on_unknown(), NewLine()))
            except DiagnosticError as diagnostic:
                rich.print(diagnostic.with_source_code(text))

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
