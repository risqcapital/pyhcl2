from __future__ import annotations

import networkx as nx  # type: ignore

from pyhcl2.nodes import Block, Module
from pyhcl2.tracker import resolve_variable_references


def get_blocks_by_generation(
    module: Module, block_type: str, reverse: bool = False
) -> list[list[Block]]:
    blocks = module.get_blocks(block_type)
    generations = _topological_generations(blocks)
    if reverse:
        generations.reverse()
    return generations


def _topological_generations(blocks: list[Block]) -> list[list[Block]]:
    blocks_by_key = {block.key(): block for block in blocks}

    graph = nx.DiGraph()

    for key, block_under_test in blocks_by_key.items():
        graph.add_node(key)
        variable_references = resolve_variable_references(block_under_test)

        for dirty_child in variable_references:
            if dirty_child in blocks_by_key:
                graph.add_edge(dirty_child, key)

    if not nx.is_directed_acyclic_graph(graph):
        raise ValueError("Graph is not a DAG")

    generations = list(nx.topological_generations(graph))

    return [[blocks_by_key[k] for k in generation] for generation in generations]
