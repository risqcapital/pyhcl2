from pyhcl2.eval import EvaluationScope, Evaluator
from pyhcl2.parse import parse_expr_or_attribute

if __name__ == "__main__":
    scope = EvaluationScope()
    show_ast = False
    while True:
        text = input("> ")

        match text:
            case "ast":
                show_ast = not show_ast
                print("Printing abstract syntax trees" if show_ast else "Not printing abstract syntax trees")
                continue
            case "exit":
                break

        try:
            ast = parse_expr_or_attribute(text)
            if show_ast:
                print(ast.pformat())
            result = Evaluator().eval(ast, scope)
            if result is not None:
                print(result)
        except Exception as e:
            print(e)
