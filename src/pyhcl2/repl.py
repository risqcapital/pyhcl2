from pathlib import Path

import rich
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from rich.console import Group, NewLine

from pyhcl2.eval import Evaluator, EvaluationScope
from pyhcl2.parse import parse_expr_or_attribute
from pyhcl2.pymiette import Diagnostic, LabeledSpan
from pyhcl2.rich_utils import Inline
from pyhcl2.values import Unresolved

if __name__ == "__main__":
    scope = EvaluationScope()
    session: PromptSession = PromptSession(history=FileHistory(Path.home() / ".pyhcl2_history"))
    try:
        while True:
            text = session.prompt("> ", auto_suggest=AutoSuggestFromHistory())

            if text == "":
                continue

            if text == "exit":
                break

            try:
                ast = parse_expr_or_attribute(text)
                result = Evaluator().eval(ast, scope)
                rich.print(Inline(result.resolve().raise_on_unresolved(), NewLine()))
            except Diagnostic as diagnostic:
                    rich.print(diagnostic.with_source_code(text))

    except KeyboardInterrupt:
        pass