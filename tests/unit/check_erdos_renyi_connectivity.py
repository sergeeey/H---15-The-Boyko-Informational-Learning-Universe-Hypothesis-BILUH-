"""Regression test for the development.yaml run failure (2026-08-13, second
defect): `generate_erdos_renyi` (graphs/generators.py) draws an exact
edge-count random graph via `nx.gnm_random_graph` with no connectivity
guarantee. `docs/estimand.md` already declares the benchmark's population
is "restricted to connected graphs upstream" -- but nothing in the code
enforced or verified that before this test. At N=64, mean degree 6
(n_edges=192, [A7]), `numpy.random.default_rng(18)` deterministically
reproduces a disconnected draw (found by brute-force seed search, not
cherry-picked from a known development.yaml failure -- the actual failing
config seed was never captured, so this is the smallest independent
reproduction, not a replay of the exact failing run).

Downstream this manifested as `propagation_front.hop_distances_from_source`
correctly refusing to proceed on an unreachable (-1) node -- so this test
pins the true point of failure (the generator's silent connectivity gap),
not the correctly-behaving downstream guard.
"""

import networkx as nx
import numpy as np

from boyko_benchmark.graphs.generators import generate_erdos_renyi


def test_generate_erdos_renyi_is_always_connected_at_known_disconnected_seed() -> None:
    """numpy_seed=18 is a brute-force-found witness that, unguarded,
    `nx.gnm_random_graph`'s exact-edge-count draw can be disconnected at
    N=64/mean-degree-6 -- exactly the (arm, N) shape development.yaml's
    grid exercises. The generator must not silently hand back a
    disconnected graph; docs/estimand.md's connected-population assumption
    must be enforced here, not merely declared."""
    n_nodes = 64
    n_edges = n_nodes * 6 // 2
    rng = np.random.default_rng(18)

    graph = generate_erdos_renyi(n_nodes, n_edges, rng)

    nx_graph = nx.from_numpy_array(graph.mask)
    assert nx.is_connected(nx_graph), (
        "generate_erdos_renyi returned a disconnected graph at a seed known "
        "to trigger it unguarded -- docs/estimand.md's connected-population "
        "assumption is not enforced"
    )


def test_generate_erdos_renyi_preserves_edge_count_when_retrying() -> None:
    """A connectivity-retry fix must not change the contract that the
    returned graph has exactly `n_edges` edges (exact gnm matching, [A12])
    -- only which specific edges are drawn may change on retry."""
    n_nodes = 64
    n_edges = n_nodes * 6 // 2
    rng = np.random.default_rng(18)

    graph = generate_erdos_renyi(n_nodes, n_edges, rng)

    assert int(graph.mask.sum()) // 2 == n_edges


def test_generate_erdos_renyi_connects_at_n1024_mean_degree_6_despite_low_success_rate() -> None:
    """[A38] regression: Milestone 7's N=1024 factorial pilot failed with
    `NetworkXAlgorithmError` after exhausting the original 20-retry cap.
    Root cause is NOT bad luck -- mean degree 6 ([A7]'s n_edges=3*n_nodes)
    is BELOW Erdos-Renyi's connectivity threshold ln(N)~=6.93 at N=1024,
    so the expected isolated-vertex count is N*e^-6~=2.5 and only ~9% of
    draws are connected (measured via prototype script: 18/200 successes
    for `numpy.random.default_rng(7024)`, the exact seed
    `run_open_pilot.py` used for size=1024/seed_index=6 -- graph_seed
    formula is `1000*seed_index+size`). This seed is a genuine
    reproduction of the actual failing run, not a brute-force search like
    the N=64 test above. With ~9% per-draw success, P(20 consecutive
    failures) ~= 0.19 -- a real, expected failure mode at this budget, not
    an anomaly. The retry cap must be large enough that this succeeds
    reliably (P(all attempts fail) << 1) without changing mean degree
    (preserves [A7]'s fixed-mean-degree-across-N convention and exact
    consistency with the 40 N<=512 points already computed under the old
    cap)."""
    n_nodes = 1024
    n_edges = n_nodes * 6 // 2
    rng = np.random.default_rng(7024)

    graph = generate_erdos_renyi(n_nodes, n_edges, rng)

    nx_graph = nx.from_numpy_array(graph.mask)
    assert nx.is_connected(nx_graph)
    assert int(graph.mask.sum()) // 2 == n_edges
