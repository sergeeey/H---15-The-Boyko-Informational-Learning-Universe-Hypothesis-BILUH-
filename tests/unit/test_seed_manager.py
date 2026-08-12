"""Unit tests for deterministic seed management [A11].

[A11]: seeds are derived via numpy.random.SeedSequence, keyed by an
explicit path (e.g. arm index, size index, replicate index) rather than
by call order - so re-running the same (master_seed, path) always yields
the same child seed regardless of what order other seeds were requested
in.
"""

import numpy as np

from boyko_benchmark.experiment.seed_manager import SeedManager


def test_same_master_and_path_yields_identical_child_seed() -> None:
    a = SeedManager(master_seed=20260811).child_seed(0, 3, 5)
    b = SeedManager(master_seed=20260811).child_seed(0, 3, 5)

    gen_a = np.random.default_rng(a)
    gen_b = np.random.default_rng(b)

    assert gen_a.random(10).tolist() == gen_b.random(10).tolist()


def test_different_path_yields_different_child_seed() -> None:
    mgr = SeedManager(master_seed=20260811)
    a = mgr.child_seed(0, 3, 5)
    b = mgr.child_seed(0, 3, 6)

    gen_a = np.random.default_rng(a)
    gen_b = np.random.default_rng(b)

    assert gen_a.random(10).tolist() != gen_b.random(10).tolist()


def test_different_master_seed_yields_different_child_seed() -> None:
    a = SeedManager(master_seed=1).child_seed(0, 0, 0)
    b = SeedManager(master_seed=2).child_seed(0, 0, 0)

    gen_a = np.random.default_rng(a)
    gen_b = np.random.default_rng(b)

    assert gen_a.random(10).tolist() != gen_b.random(10).tolist()


def test_child_seed_is_order_independent() -> None:
    mgr1 = SeedManager(master_seed=42)
    first_then_second = (mgr1.child_seed(1, 0), mgr1.child_seed(2, 0))

    mgr2 = SeedManager(master_seed=42)
    second_then_first = (mgr2.child_seed(2, 0), mgr2.child_seed(1, 0))

    gen_a1 = np.random.default_rng(first_then_second[0]).random(5).tolist()
    gen_a2 = np.random.default_rng(second_then_first[1]).random(5).tolist()
    assert gen_a1 == gen_a2

    gen_b1 = np.random.default_rng(first_then_second[1]).random(5).tolist()
    gen_b2 = np.random.default_rng(second_then_first[0]).random(5).tolist()
    assert gen_b1 == gen_b2


def test_child_generator_returns_usable_numpy_generator() -> None:
    gen = SeedManager(master_seed=7).child_generator(0, 0)
    assert isinstance(gen, np.random.Generator)
    values = gen.random(3)
    assert values.shape == (3,)
