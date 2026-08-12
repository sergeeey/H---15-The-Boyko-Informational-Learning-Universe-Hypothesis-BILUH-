# Novelty Check — BILUH / boyko-benchmark

FL Step -3 artifact (AI-Hypothesis Pre-Gate, mandatory before EstimandOps for
an AI-assisted research claim). Produced 2026-08-11 by an isolated
general-purpose research agent with WebSearch/WebFetch, no session context
about the internal design choices in `mathematical_contract.md` — an
independent literature sweep, not a self-serving lit-review.

**Method:** 12 search rounds, 21 sources checked, each row below cites a URL
actually retrieved. `[VERIFIED-fetched]` = abstract/page fetched via
WebFetch. `[VERIFIED-search-snippet]` = confirmed only at search-result
level (title/claim), not fetched. `[UNKNOWN]` = excluded from the verdict
basis.

## Prior-art table

| Work | Year | Source | Mechanism | Measured | Overlap | Key difference |
|---|---|---|---|---|---|---|
| Vanchurin, "The world as a neural network" | 2020 | arxiv.org/abs/2008.01540 [VERIFIED-fetched] | Learning dynamics (trainable vs hidden vars); QM≈stochastic dynamics of trainable vars | Nothing numerical — analytic mapping only | Conceptual parent of BILUH's slow/fast duality | Purely analytic, no simulation, no benchmark, no controls, no FSS |
| Katsnelson & Vanchurin, "Emergent Quantumness in Neural Networks" | 2020/21 | arxiv.org/abs/2012.05082 [VERIFIED-fetched] | Grand-canonical NN ensemble; Schrödinger eq. derived from free energy | Analytic only | "Schrödinger from a learning system" motif | No simulations, no geometry, no spectral dimension |
| Vanchurin, "Towards a theory of machine learning" | 2020 | arxiv.org/abs/2004.09280 [VERIFIED-search-snippet] | Thermodynamics of learning | Analytic | Background theory for "learning" framing | No graph geometry, no numerics |
| Vanchurin, "Towards a theory of quantum gravity from neural networks" | 2021 | arxiv.org/abs/2111.00903 [VERIFIED-fetched] | Entropy production/destruction → emergent Lorentz symmetry/curvature | Analytic | Directly claims emergent spacetime from NN learning | No numerical simulation, no geometry measurement, no controls, no FSS |
| Vanchurin, "Geometric Learning Dynamics" | 2025 | arxiv.org/abs/2504.14728 [VERIFIED-fetched] | Learning regimes via metric-noise power laws | Analytic | Learning↔quantum regime mapping | No graphs, no spectral dimension, no computation |
| Alexander et al., "The Autodidactic Universe" | 2021 | arxiv.org/abs/2104.03902 [VERIFIED-fetched] | Matrix models ↔ gauge/gravity ↔ learning correspondence | Conceptual (79pp) | "Learning universe" framing | No emergent-dimension measurement, no benchmark/controls/FSS |
| Konopka, Markopoulou, Smolin, "Quantum Graphity" | 2006 | arxiv.org/abs/hep-th/0611197 [VERIFIED-fetched] | Dynamical graph, symmetry breaking → low-dim lattice | Emergent locality, mean distances | Dynamical graph → emergent dimensionality (shared goal) | Thermal/Hamiltonian mechanism, not Hebbian; no matched controls |
| Konopka, Markopoulou, Severini, "Quantum Graphity: emergent locality" | 2008 | arxiv.org/abs/0801.0861 [VERIFIED-search-snippet] | Same + string-net condensation | Emergent locality | Same as above | Same as above |
| Caravelli et al., geometrogenesis numerics | 2015 | arxiv.org/abs/1506.07588 [VERIFIED-search-snippet] | Numerical graphity study | Found problems w/ the transition | Confirms field does test graphity numerically | No Hebbian rules, no control battery |
| Trugenberger, "Combinatorial Quantum Gravity" | 2016/17 | arxiv.org/abs/1610.05934 [VERIFIED-fetched] | Ollivier-Ricci curvature action; random→geometric phase transition | Curvature, phase structure, EH action at scale | Emergent geometry from dynamical graph | Equilibrium statistical action (Metropolis), not local adaptive rule |
| Kelly, Trugenberger, Biancalana, "Self-Assembly of Geometric Space" | 2019 | arxiv.org/abs/1901.09870 [VERIFIED-fetched] | Monte Carlo, Ollivier-curvature discretized EH action | Continuous phase transition; action-minimizing complexes | **Closest QG neighbor on observables:** dynamical graphs + numerics + scaling | No Hebbian/learning rule, no Schrödinger coupling, no control-arm screen |
| Kelly, Trugenberger, Biancalana, "Emergence of the circle…" | 2021 | iopscience 10.1088/1361-6382/abe2d8 [VERIFIED-search-snippet] | Same program, cubic random graphs | **Hausdorff AND spectral dimension measured numerically** | Direct observable overlap | Equilibrium MC, no adaptation, no control-arm discipline |
| Ambjørn, Jurkiewicz, Loll, "Spectral Dimension of the Universe" (CDT) | 2005 | arxiv.org/abs/hep-th/0505113 [VERIFIED-fetched] | Monte Carlo over causal triangulations | Scale-dependent d_s: ~4 large, ~2 short | **Strongest observable-level precedent** | Ensemble gravity path integral, not adaptive weights + unitary dynamics; no controls |
| CDT FSS follow-ups | 2017-2019 | arxiv.org/abs/1711.02685, 1812.09331 [VERIFIED-search-snippet] | CDT | Scaling/dimensional-reduction analyses | FSS of spectral dim is standard CDT practice | FSS for estimation, not preregistered pass/fail gates; no controls |
| Eichhorn & Mizera, causal-set spectral dimension | 2013 | arxiv.org/abs/1311.2530 [VERIFIED-fetched] | Random walks on sprinkled causal sets | d_s increases at small scale; proposed as manifoldlikeness discriminator | Uses spectral dim as a discriminator — closest in spirit to a gate | Not dynamically adapting; no Hebbian rule; no control battery |
| Wolfram Physics Project, dimension notion | 2020 | wolframphysics.org […]/the-notion-of-dimension/ [VERIFIED-fetched] | Hypergraph rewriting rules | Volume-growth dimension exponent | Dynamical discrete structure → emergent dimension | No spectral dimension, no negative controls (confirmed on their own page), no adaptation |
| Bianconi & Rahmede, network geometry with flavor | 2015+ | arxiv.org/abs/1511.04539, pdf/2001.05934 [VERIFIED-search-snippet] | Growing simplicial complexes | Emergent hyperbolic geometry; higher-order spectral dim | Spectral dim of evolving discrete structures | Growth/attachment rules, not Hebbian; no Schrödinger coupling; no control screen |
| Jarman, Steur, Trengove, Tyukin, van Leeuwen, adaptive rewiring | 2017 | pmc.ncbi.nlm.nih.gov/articles/PMC5640682 (Sci. Rep.) [VERIFIED-fetched] | **Adaptive rewiring driven by heat kernel e^(-tℒ), normalized Laplacian** — closest mechanism neighbor | Small-worldness, modularity, centrality; 100 runs; vs. Watts-Strogatz/Erdős-Rényi | Adaptation + Laplacian dynamics + explicit random-control comparisons | **Classical diffusion, not Schrödinger**; network-science observables, no spectral dimension, no FSS |
| Trugenberger, "Networks as the fundamental constituents" (review) | 2025/26 | arxiv.org/abs/2512.17676 [VERIFIED-fetched] | Review of combinatorial QG program | Qualitative | Confirms current field state | No adaptive dynamics, no benchmark/controls framework |
| Lamas, "Emergent spectral geometry in the Coherence-Curvature Model" | 2025 | arxiv.org/abs/2511.13423 [VERIFIED-fetched] | **Closest recent neighbor.** Dynamical graph ensemble; Hamiltonian = algebraic connectivity + Ollivier-Ricci + edge penalty; simulated annealing | **d_s ~ 4 at largest sizes, with finite-size scaling**; code on Zenodo | Spectral dimension + FSS on dynamical graphs, open code | Annealing on a designed Hamiltonian — no Hebbian/learning rule, no unitary fast dynamics, no frozen/scrambled/alt-objective arms, no preregistered gates evident |
| "Hebbian Physics Networks" | 2025 | arxiv.org/pdf/2507.00641 [VERIFIED-search-snippet] | Anti-Hebbian adaptation enforcing local physical laws (PDE solving) | Physical-consistency emergence | "Hebbian weights self-organize structure" motif | Aimed at PDE computation, not emergent spacetime; spectral dimension [UNKNOWN — not fetched] |
| Open emergent-spacetime benchmark suite | — | targeted search, no hit | — | — | — | **None found.** One search family only → treat as [WEAK] negative |

## Delta analysis

- **d1 — Control-arm discipline (frozen / matched-random / scrambled / alt-objective) applied to emergent-geometry claims: SURVIVES**, with a qualifier — no QG program (CDT, combinatorial QG, graphity, Wolfram, causal sets, NGF) runs matched negative controls against its geometrogenesis observables (confirmed absent even on Wolfram's own methods page). The qualifier: control-arm discipline itself is not new — it exists in the adjacent adaptive-network literature (Jarman et al. compare against Watts-Strogatz/Erdős-Rényi). The delta is specifically "controls applied to *spacetime-emergence* observables," not "controls in adaptive networks."
- **d2 — Hebbian weight adaptation coupled to unitary Schrödinger dynamics as the geometrogenesis mechanism: SURVIVES, narrowed 2026-08-11 (DDD skeptic finding #7).** Targeted searches for this exact coupling found nothing. The two halves exist separately — adaptive rewiring driven by *classical* heat diffusion (Jarman/van Leeuwen), and spectral-dimension measurement on graphs made dynamical by *equilibrium statistical* dynamics (CDT, Kelly-Trugenberger-Biancalana, Lamas) — but nowhere coupled. **Narrowing, per skeptic review:** Jarman et al. is not a distant relative here — it uses adaptive rewiring driven by the *same* normalized-Laplacian heat kernel this contract's §5.1 uses, making it directly-adjacent prior art for the *mechanism class* (Laplacian-driven adaptive rewiring), not just for "adaptive networks" generally. If BILUH's Gate-A signature turns out to appear under *any* Laplacian-driven adaptive rule regardless of whether the carrier dynamics is classical diffusion or unitary Schrödinger evolution, then the unitary coupling is not the load-bearing source of novelty — the adaptive-Laplacian rewiring itself would be, and Jarman's 2017 result becomes the closer prior art, not a background citation. **This is not decidable from a literature scan; it is decidable from a 7th control arm** (classical-diffusion-driven Hebbian adaptation, holding the adaptation rule's structure and the control-arm battery fixed, varying only the carrier dynamics). **Update 2026-08-11: the user requested this arm be added.** Arm CD (Classical Diffusion Control) is now part of the Stage-1 design — `mathematical_contract.md` §2.2, §3.2 (`ClassicalHebbianAdaptation`, `[A18]`), §4; `estimand.md`'s comparator table; `falsification_gates.md` (not a G6 gate, parallel role to Arm F). Whether d2's unitary-coupling claim survives is now an empirical question the benchmark itself answers, not an open scope decision — if Active and Arm CD produce the same geometric signature, d2 should be downgraded at the results stage (per the Minimal Relaxation Rule, not by editing this document retroactively).
- **d3 — Preregistered FSS gates + verdict machine (SURVIVES/FAILS): SURVIVES.** FSS is standard *estimation* practice in CDT/combinatorial QG, never used there as a preregistered pass/fail gate with matched controls deciding a verdict. Eichhorn & Mizera's "discriminator" framing is the closest conceptual relative, not a protocol.
- **d4 — Benchmark as reusable lab for third-party claims: SURVIVES, weakly held [WEAK]** — absence-of-evidence from one search family only, not a load-bearing novelty pillar.

## Kill question

**Has anyone already run essentially this experiment? NO for the conjunction; PARTIAL for component pairs.**
Adaptive weights + Laplacian dynamics: yes, but classical diffusion, no spectral dimension (Jarman 2017). Dynamical graphs + spectral dimension + FSS: yes (CDT 2005; Kelly-Trugenberger-Biancalana 2021; Lamas 2025), but equilibrium/annealing dynamics, no adaptation, no controls. Learning + Schrödinger/gravity: yes, analytically only (Vanchurin program, 4 papers, all confirmed zero simulations). **The full triple — Hebbian adaptation × unitary fast dynamics × matched-control + FSS-gated verdict — not found in any retrieved source.**

## Verdict: PARTIAL-OVERLAP (mechanism and methodology deltas survive as novel)

Every individual *observable* here is well-trodden — heat-kernel spectral
dimension on dynamical discrete structures is 20 years old (CDT 2005) and
was measured with FSS as recently as November 2025 (Lamas). Claiming novelty
for "measuring emergent spectral dimension from a dynamical graph" would be
a rediscovery — **do not make that claim**. What survives this scan as
genuinely unfound: (i) Hebbian slow weight dynamics coupled to unitary
Schrödinger fast dynamics as the geometrogenesis mechanism (d2), and (ii)
matched negative-control arms plus preregistered FSS gates producing a
SURVIVES/FAILS verdict, applied to emergent-spacetime observables (d1+d3).
Vanchurin's program, which BILUH's framing descends from, is confirmed
analytic across all four papers checked — this benchmark would be the first
computational falsification-style test of that idea class found in this
scan.

## Mandatory citations for claim.md / any future publication

- Cite as direct prior art for the *observables*: Ambjørn/Jurkiewicz/Loll
  (CDT, hep-th/0505113), Kelly/Trugenberger/Biancalana (1901.09870 +
  the circle-emergence follow-up), **Lamas 2511.13423 (closest neighbor —
  re-verify full text before publication, only the abstract was checked
  here)**.
- Cite as the conceptual origin of the "learning universe" framing:
  Vanchurin 2008.01540, and acknowledge explicitly that his program is
  analytic — BILUH is a proposed computational test, not a continuation of
  numerics that already exist there.
- Cite as nearest mechanism-level neighbor: Jarman et al. 2017
  (PMC5640682) — adaptive rewiring via the same normalized-Laplacian heat
  kernel this contract uses (§5.1), but classical diffusion, not the
  unitary Schrödinger coupling this project adds.
- Do **not** claim novelty for: spectral dimension as a concept, heat-kernel
  estimators, FSS methodology in general, or "dynamical graphs produce
  emergent geometry" as a general research direction.

## Open caveats

1. Lamas 2511.13423's Zenodo code was not inspected — only the abstract was
   verified. Its actual implementation could narrow d4 further; re-check
   before any external claim.
2. Kelly-Trugenberger-Biancalana's spectral-dimension numbers are
   `[VERIFIED-search-snippet]` only, not fetched in full.
3. The "no existing benchmark suite" claim (d4) rests on one search family
   — hold at `[WEAK]`, do not present as a settled fact.
