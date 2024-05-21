from pyhcl2.eval import EvaluationScope, Evaluator
from pyhcl2.parse import parse_expr_or_attribute

if __name__ == "__main__":
    scope = EvaluationScope()
    while True:
        text = input("> ")

        if text == "exit":
            break

        try:
            ast = parse_expr_or_attribute(text)
            result = Evaluator().eval(ast, scope)
            if result is not None:
                print(result)
        except Exception as e:
            print(e)
