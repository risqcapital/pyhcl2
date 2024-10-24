# Changelog

## [1.0.0](https://github.com/risqcapital/pyhcl2/compare/v0.2.1...v1.0.0) (2024-10-24)


### ⚠ BREAKING CHANGES

* Migrate to Value class types instead of primative types for results ([#40](https://github.com/risqcapital/pyhcl2/issues/40))
* Add `start_pos` and `end_pos` to AST Nodes, tweak grammar and simplify test harness ([#37](https://github.com/risqcapital/pyhcl2/issues/37))

### Features

* Add `start_pos` and `end_pos` to AST Nodes, tweak grammar and simplify test harness ([#37](https://github.com/risqcapital/pyhcl2/issues/37)) ([5b769b1](https://github.com/risqcapital/pyhcl2/commit/5b769b141e49c2076f400c01e5bf320e563bfc24))
* Migrate to Value class types instead of primative types for results ([#40](https://github.com/risqcapital/pyhcl2/issues/40)) ([dff6ff5](https://github.com/risqcapital/pyhcl2/commit/dff6ff5d444aef08596ceedc8b1a0fd664a9e0f7))
* Support syntax highlighting ([#45](https://github.com/risqcapital/pyhcl2/issues/45)) ([6e821e6](https://github.com/risqcapital/pyhcl2/commit/6e821e6de0de8f66c946232b86c50367791deadd))

## [0.2.1](https://github.com/risqcapital/pyhcl2/compare/v0.2.0...v0.2.1) (2024-07-04)


### Bug Fixes

* Hack around VisitedVariablesTracker on get index ([#18](https://github.com/risqcapital/pyhcl2/issues/18)) ([58582a7](https://github.com/risqcapital/pyhcl2/commit/58582a75d3ffb3d79c97899bdea3914b710ea5a6))

## [0.2.0](https://github.com/risqcapital/pyhcl2/compare/v0.1.0...v0.2.0) (2024-07-04)


### Features

* Evaluate intrinsic function calls ([#16](https://github.com/risqcapital/pyhcl2/issues/16)) ([67cd08f](https://github.com/risqcapital/pyhcl2/commit/67cd08f0a917648ed9faf2f8b3c6f45057b1043a))

## 0.1.0 (2024-05-31)


### ⚠ BREAKING CHANGES

* Rewrite transformer with full support for hcl2, modifies ast

### Features

* Add default EvaluationScope value ([01ce562](https://github.com/risqcapital/pyhcl2/commit/01ce5622a0e5bfd5ce1b5e69f09318a77bd8137a))
* Add evaluator and tracker ([d3b4065](https://github.com/risqcapital/pyhcl2/commit/d3b4065f180cb9293381da459e2a4d2d885a0e23))
* Add helpers for attributes and blocks on Block ([210f53e](https://github.com/risqcapital/pyhcl2/commit/210f53ebae2dd373dfb4184d04df63f596d8f699))
* Add helpers to get block of a specific type ([3da3778](https://github.com/risqcapital/pyhcl2/commit/3da37787b29fa883ee7ea58892b09ba7b326f984))
* Add key_path property to Stmt and remove pformat code ([24b5cce](https://github.com/risqcapital/pyhcl2/commit/24b5cce12d666e30811a60499f1187de9b0ea3e2))
* Add support for operator precedence ([8d8ee1f](https://github.com/risqcapital/pyhcl2/commit/8d8ee1f589406910f95a1e9a226008ee4018f909))
* Add topological generations logic ([1238201](https://github.com/risqcapital/pyhcl2/commit/123820114aab7877c8fb3a5ba2295c1a5b6d19a3))
* Allow filtering by labels with get_block call ([dd09a65](https://github.com/risqcapital/pyhcl2/commit/dd09a65628620e89be25d81d655366e863221b0f))
* Eval Blocks within blocks as arrays to allow multiple definitions for the same key ([0a69146](https://github.com/risqcapital/pyhcl2/commit/0a69146068b520952e68ecb6c191dfc49489e039))
* Eval Blocks within blocks as arrays to allow multiple definitions for the same key ([b79620a](https://github.com/risqcapital/pyhcl2/commit/b79620a9e037e0ed34eb32d2b9bd57bd72a9852d))
* Improve tests and fix bugs in transformer ([fe475de](https://github.com/risqcapital/pyhcl2/commit/fe475de1b5aab0777420e3221c47d110fd251d03))
* Parsing of pydantic models from hcl ([9079b0b](https://github.com/risqcapital/pyhcl2/commit/9079b0be9a65098f7cba02b33e36573608cf3dda))
* Return value from eval_block and eval_attribute ([2a9625f](https://github.com/risqcapital/pyhcl2/commit/2a9625f8a55ef6666790988942b928358b89eb0d))
* Rewrite transformer with full support for hcl2, modifies ast ([1bfe882](https://github.com/risqcapital/pyhcl2/commit/1bfe882578193887b8651f887a02e84670320eb9))
* Update var tracker with api ([ba82789](https://github.com/risqcapital/pyhcl2/commit/ba8278937b295ade0a407c8316c15dc62def5647))
* Use set for variables tracker ([704cb39](https://github.com/risqcapital/pyhcl2/commit/704cb39eb4a5168117954afeae12d1ee61c88712))


### Bug Fixes

* Discard ([02636d5](https://github.com/risqcapital/pyhcl2/commit/02636d5c33694ed81c71a611a513ad69f9c3bca5))
* e.errors instead of e.messages ([9719a0a](https://github.com/risqcapital/pyhcl2/commit/9719a0a97985a3403d80d2c7c4bf0c3628e4e987))
* Fix eval issues and add tests ([8003a11](https://github.com/risqcapital/pyhcl2/commit/8003a119b6cdc1cc5b7057dd9d4c0d2c0bb23087))
* Fix parsing of function calls (`FunctionCall.name` is now correctly populated with a string), added a respective unit test ([480d47b](https://github.com/risqcapital/pyhcl2/commit/480d47bdbe774d4b9063b9c2a06f38ad1848e25e))
* Pydantic is not a dev dependency ([eacb0e3](https://github.com/risqcapital/pyhcl2/commit/eacb0e37d6168b3538b50783b42a3e1b238e9905))
* Recursive forward reference for Value type and allow literal strings as dict keys ([85e4f73](https://github.com/risqcapital/pyhcl2/commit/85e4f7355d61a111b40641321ab0e4f7d3162ae3))
* ruff ([2a56f4b](https://github.com/risqcapital/pyhcl2/commit/2a56f4b7bbc1198e5691d8a3881b2abb1ad2f07a))
* TypeError for invalid type exception ([5f0dcb1](https://github.com/risqcapital/pyhcl2/commit/5f0dcb15923d6e327cbb5d89d4b7aa76c25e0b3c))


### Documentation

* Fix readme ([d453d7f](https://github.com/risqcapital/pyhcl2/commit/d453d7f879ef8427d73b64628de64e114b947b8b))
