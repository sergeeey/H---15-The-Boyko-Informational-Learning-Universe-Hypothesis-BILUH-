#!/usr/bin/env python
"""K1 feasibility-only audit (user-directed, 2026-08-18, following `[A57]`'s
100%-disconnection finding) -- NOT a science run. No `R_edge`, no G1, no
curvature. The only question this script answers: WHERE, mechanically,
does `RateBasedTopologyRule` break connectivity at `docs/v4_spec.md`
Sec7/Sec11's exact frozen parameters (rho=0.01, m=3, N=512, 10% damage,
same 5 seeds/master_seed as the M2 campaign)?

Reuses the exact same damaged lattice each seed produces in M2
(`experiment/k1_damage_gate.py`'s seed-stream derivation, same stream
indices 0/1/2, replicated here rather than imported since they're
private to that module) -- this is the SAME substrate `[A57]` measured,
not a fresh draw.

Runs only A3 (`CorrelationScorer`) per seed: pruning is driven purely by
`graph.weights` (persistence-tracked lowest-weight edges), which the
regrow scorer never influences -- confirmed by M2's own data
(`trunc(A3)==trunc(A4)==2` on every seed) and by reading `RateBased
TopologyRule.update` (`dynamics/topology_v4.py:196`, `low_set` is sorted
by `graph.weights` alone). A4 would disconnect identically up to the
point the two arms' regrowth choices first diverge, which -- since
disconnection happens at window 2, the EARLIEST window any edge can
satisfy `m=3`'s persistence requirement -- is after this audit's own
disconnection event, not before it. Running only A3 halves the compute
for no loss of diagnostic power.

Distinguishes three hypotheses named by the user:
  H_rho          -- the rho-quantile batch itself (n_target) is too large
  H_early        -- pruning starts before C_ij is informative (windows
                    0-1 have zero adaptation exposure when m=3 requires
                    3 consecutive low-set windows before eligibility)
  H_concentration -- Top-K-selected prunes concentrate on few nodes
                     (checked directly: how many of the pruned edges are
                     BRIDGES of the pre-window graph, and how many prunes
                     land on the single most-affected node)

Also empirically confirms (not just claims) that connectivity is checked
after the FULL atomic prune+regrow operation, never at an intermediate
prune-only state -- reconstructs the intermediate mask externally (via
set difference, no changes to production code) and reports both.
"""

import sys

import networkx as nx
import numpy as np
from numpy.typing import NDArray

from boyko_benchmark.dynamics.adaptive import HebbianAdaptation, StateTrajectory
from boyko_benchmark.dynamics.backend import ClosedUnitaryBackend
from boyko_benchmark.dynamics.topology_v4 import CorrelationScorer, RateBasedTopologyRule
from boyko_benchmark.experiment.runner import ADAPTATION_DTAU, localized_psi0
from boyko_benchmark.experiment.seed_manager import SeedManager
from boyko_benchmark.graphs.damage import corrupt_lattice_edges
from boyko_benchmark.graphs.lattice import generate_periodic_cubic_lattice, lattice_coordinates
from boyko_benchmark.graphs.weights import normalized_laplacian

N_SIDE_LENGTH = 8  # N = 512, matches M2
N_SEEDS = 5
DAMAGE_FRACTION = 0.10
RHO = 0.01
M_PERSISTENCE = 3
ETA = 0.1
DT = 0.05
K_SUBSTEPS = 50
MASTER_SEED = 20260818  # identical to M2 -- SAME damaged lattices
MAX_WINDOWS = 6  # M2 found disconnection at window 2 on every seed; margin only

# Stream indices replicated from experiment/k1_damage_gate.py (private there)
_DAMAGE_STREAM = 0
_TIEBREAK_STREAM = 1
_REGROWTH_STREAM = 2

Edge = tuple[int, int]


def edge_set(mask: NDArray[np.bool_]) -> frozenset[Edge]:
    return frozenset((int(i), int(j)) for i, j in np.argwhere(np.triu(mask)))


def mask_from_edges(n_nodes: int, edges: frozenset[Edge]) -> NDArray[np.bool_]:
    mask = np.zeros((n_nodes, n_nodes), dtype=bool)
    for i, j in edges:
        mask[i, j] = mask[j, i] = True
    return mask


def to_networkx(mask: NDArray[np.bool_]) -> "nx.Graph[int]":
    graph: nx.Graph[int] = nx.Graph()
    graph.add_nodes_from(range(mask.shape[0]))
    graph.add_edges_from((int(i), int(j)) for i, j in np.argwhere(np.triu(mask)))
    return graph


def largest_component_size(mask: NDArray[np.bool_]) -> int:
    graph = to_networkx(mask)
    return max((len(c) for c in nx.connected_components(graph)), default=0)


def is_connected(mask: NDArray[np.bool_]) -> bool:
    return bool(largest_component_size(mask) == mask.shape[0])


def min_degree(mask: NDArray[np.bool_]) -> int:
    return int(mask.sum(axis=1).min())


def audit_one_seed(seed_index: int) -> None:
    seed_manager = SeedManager(MASTER_SEED)
    graph = generate_periodic_cubic_lattice(N_SIDE_LENGTH)
    coords = lattice_coordinates(N_SIDE_LENGTH)
    center_coord = np.array([N_SIDE_LENGTH // 2] * 3)
    center_index = int(np.argmin(np.sum((coords - center_coord) ** 2, axis=1)))
    psi0 = localized_psi0(graph.n_nodes, center_index)

    damage_rng = seed_manager.child_generator(seed_index, _DAMAGE_STREAM)
    damaged_graph, _damaged_out = corrupt_lattice_edges(graph, damage_rng, DAMAGE_FRACTION)

    tiebreak_seed = int(seed_manager.child_seed(seed_index, _TIEBREAK_STREAM).generate_state(1)[0])
    regrowth_seed = int(seed_manager.child_seed(seed_index, _REGROWTH_STREAM).generate_state(1)[0])
    rule = RateBasedTopologyRule(
        rho=RHO,
        m=M_PERSISTENCE,
        regrow_scorer=CorrelationScorer(),
        topology_tiebreak_seed=tiebreak_seed,
        control_regrowth_seed=regrowth_seed,
    )
    adaptation_rule = HebbianAdaptation(eta=ETA)
    backend = ClosedUnitaryBackend()

    print(f"\n=== seed {seed_index} ===")
    header = (
        f"{'win':>3} {'n_edge':>6} {'plan':>4} {'prune':>5} {'regrow':>6} "
        f"{'max/node':>8} {'bridges':>7} {'pruned_bridges':>14} "
        f"{'mindeg_pre':>10} {'mindeg_mid':>10} {'mindeg_fin':>10} "
        f"{'lcc_pre':>7} {'lcc_mid':>7} {'lcc_fin':>7} {'conn_mid':>8} {'conn_fin':>8}"
    )
    print(header)

    graph = damaged_graph
    psi = psi0
    for window_index in range(MAX_WINDOWS):
        hamiltonian = normalized_laplacian(graph)
        states = backend.evolve(hamiltonian, psi, DT, K_SUBSTEPS, 0.0, 0.0, None)
        trajectory = StateTrajectory(states=states)
        graph = adaptation_rule.update(graph, trajectory, ADAPTATION_DTAU)

        pre_mask = graph.mask
        edges_pre = edge_set(pre_mask)
        n_edges_pre = len(edges_pre)
        planned = max(1, round(RHO * n_edges_pre)) if n_edges_pre > 0 else 0

        pre_nx = to_networkx(pre_mask)
        pre_connected = nx.is_connected(pre_nx)
        # networkx's stub mis-types bridges() as Iterator[int]; runtime-
        # verified (.venv/Scripts/python.exe -c "...") it actually yields
        # 2-tuples of node ids, same shape as edges().
        raw_bridges: list[tuple[int, int]] = list(nx.bridges(pre_nx)) if pre_connected else []  # type: ignore[arg-type]
        bridges: frozenset[Edge] = frozenset((int(a), int(b)) for a, b in raw_bridges)

        graph_after = rule.update(graph, trajectory, ADAPTATION_DTAU)
        edges_after = edge_set(graph_after.mask)
        pruned = edges_pre - edges_after
        regrown = edges_after - edges_pre
        intermediate_edges = edges_pre - pruned  # reconstructed, no prod-code changes
        intermediate_mask = mask_from_edges(graph.n_nodes, intermediate_edges)
        final_mask = graph_after.mask

        node_prune_counts: dict[int, int] = {}
        for i, j in pruned:
            node_prune_counts[i] = node_prune_counts.get(i, 0) + 1
            node_prune_counts[j] = node_prune_counts.get(j, 0) + 1
        max_per_node = max(node_prune_counts.values(), default=0)

        pruned_bridges = pruned & {tuple(sorted(b)) for b in bridges}

        conn_mid = is_connected(intermediate_mask)
        conn_fin = is_connected(final_mask)

        print(
            f"{window_index:>3} {n_edges_pre:>6} {planned:>4} {len(pruned):>5} {len(regrown):>6} "
            f"{max_per_node:>8} {len(bridges):>7} {len(pruned_bridges):>14} "
            f"{min_degree(pre_mask):>10} {min_degree(intermediate_mask):>10} "
            f"{min_degree(final_mask):>10} "
            f"{largest_component_size(pre_mask):>7} {largest_component_size(intermediate_mask):>7} "
            f"{largest_component_size(final_mask):>7} {str(conn_mid):>8} {str(conn_fin):>8}"
        )

        graph = graph_after
        psi = states[-1]
        if not conn_fin:
            first_break = (
                "intermediate (prune already broke it)"
                if not conn_mid
                else "final (regrow re-broke a healed graph -- edge-budget invariant violated?)"
            )
            print(f"    -> disconnected this window. First lost at: {first_break}")
            if pruned_bridges:
                print(
                    f"    -> {len(pruned_bridges)}/{len(pruned)} pruned edges were BRIDGES "
                    f"of the pre-window graph -- concentration/bridge-targeting signal"
                )
            break


def main() -> int:
    print("=== K1 feasibility-only audit (no R_edge/G1/curvature) ===")
    print(
        f"N={N_SIDE_LENGTH**3}, rho={RHO}, m={M_PERSISTENCE}, damage={DAMAGE_FRACTION}, "
        f"eta={ETA}, dt={DT}, K={K_SUBSTEPS}, master_seed={MASTER_SEED}, arm=A3 only"
    )
    for seed_index in range(N_SEEDS):
        audit_one_seed(seed_index)
    return 0


if __name__ == "__main__":
    sys.exit(main())
