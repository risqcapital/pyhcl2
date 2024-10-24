# pyhcl2

`pyhcl2` is a python based interpreter library for the [HCL 2](https://github.com/hashicorp/hcl) configuration language used by [Terraform](https://www.terraform.io/) and other tools.

## Features

- Parse HCL files or expressions into an AST (Abstract Syntax Tree).
- Generate topological generations of blocks based on dependencies.
- Evaluate the AST Nodes with a given set of variables and intrinsic functions.
- Transform the AST Nodes into a Pydantic Model, with validation.

## Credits
This project is based on work by
- [HashiCorp (hashicorp/hcl)](https://github.com/hashicorp/hcl)
- [Niklas Rosenstein (NiklasRosenstein/python-hcl2-ast)](https://github.com/NiklasRosenstein/python-hcl2-ast)
- [Amplify Education (amplify-education/python-hcl2)](https://github.com/amplify-education/python-hcl2)
