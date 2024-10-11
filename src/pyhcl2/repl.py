from pathlib import Path

import rich
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from rich.console import NewLine

from pyhcl2.eval import Evaluator, EvaluationScope
from pyhcl2.parse import parse_expr_or_attribute
from pyhcl2.pymiette import Diagnostic
from pyhcl2.rich_utils import Inline

def main() -> None:
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

if __name__ == "__main__":
    main()