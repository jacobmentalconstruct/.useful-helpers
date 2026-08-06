"""hot_engine.py — GraphBLAS activation propagation (The Reactor).

Ownership: core/engine/inference/hot_engine.py
    Executes the physiological update loop over a localized subgraph
    loaded from the Cold Artifact.

Update equation (per HyperNeuron_MathAndProcess.md):
    h_{t+1} = α·h_t + A·h_t - H·h_t

Where:
    h  = live activation vector  [0.0, 1.0] per node
    α  = decay multiplier (default 0.9 — friction / dissipation)
    A  = adjacency matrix (pull + precedes edges → excitatory)
    H  = inhibition matrix (occurrence-level contradiction pressure)

Inhibition Bridge:
    H is populated from ``subgraph["inhibit_occ_pairs"]`` — occurrence-level
    pairs whose SVD vectors are anti-correlated (|cosine| > 0.2, computed by
    retrieval.load_subgraph).  This bridges the token-level NPMI signal
    (stored in inhibit_edges) into the occurrence-level index space used by
    the Hot Engine, without requiring a separate token→occurrence lookup table.

Cyclic Prevention (Builder Contract §3.2):
    A boolean mask excludes the originating seed nodes from receiving
    back-propagated energy:  h_next[~mask] = α·h + A·h - H·h
    Combined with a hard hop-limit and decay, the propagation terminates.

Output: Bag of Evidence — ranked list of (occurrence_id, activation) pairs.

Boundary rule: this module NEVER writes to disk.  All state is ephemeral.
It does not import from assembler or surveyor.

GraphBLAS availability:
    If python-graphblas is installed, uses sparse matrix-vector multiply.
    Falls back to a pure numpy dense implementation automatically.

V1 reference: _BDHyperNeuronEMITTER/src/engine/inference/hot_engine.py
V1 changes (none — physics preserved identically):
    - Module docstring updated to v2 context
    - No mathematical or algorithmic changes
"""

from __future__ import annotations

from typing import Dict, List, NamedTuple, Optional, Tuple

# ── GraphBLAS / numpy backend selector ───────────────────────────────

try:
    import graphblas as gb  # type: ignore[import]
    _HAS_GRAPHBLAS = True
except ImportError:
    _HAS_GRAPHBLAS = False

import numpy as np


# ── Output type ───────────────────────────────────────────────────────

class BagOfEvidence(NamedTuple):
    """Ranked activation result from one query propagation."""
    occurrence_id: str
    activation: float
    hunk_id: str
    node_kind: str
    attention_weight: float
    static_mass: int


# ── Core engine ───────────────────────────────────────────────────────

class HotEngine:
    """Executes the physiological update loop over a subgraph dict.

    Parameters
    ----------
    decay : float
        Friction multiplier α ∈ (0, 1).  Default 0.9.
    hop_limit : int
        Maximum propagation steps.  Default 2 (sufficient for local BoE).
    inhibit_scale : float
        Scalar applied to the inhibition matrix H.  Default 1.0.
    """

    def __init__(
        self,
        decay: float = 0.9,
        hop_limit: int = 2,
        inhibit_scale: float = 1.0,
    ) -> None:
        if not 0.0 < decay < 1.0:
            raise ValueError(f"decay must be in (0, 1), got {decay}")
        self.decay = decay
        self.hop_limit = hop_limit
        self.inhibit_scale = inhibit_scale

    def run(
        self,
        subgraph: dict,
        seed_occurrence_ids: List[str],
        top_k: int = 20,
    ) -> List[BagOfEvidence]:
        """Run the update loop and return a ranked Bag of Evidence.

        Parameters
        ----------
        subgraph : dict
            Output of ``retrieval.load_subgraph()``.  Must contain keys
            ``"nodes"``, ``"edges"``, and optionally ``"inhibit_occ_pairs"``.
        seed_occurrence_ids : list[str]
            The anchor occurrence_ids injected with initial activation 1.0.
        top_k : int
            Maximum results to return.

        Returns
        -------
        list[BagOfEvidence]
            Ranked by final activation, descending.
        """
        nodes = subgraph["nodes"]
        edges = subgraph["edges"]                       # (src, op, tgt, weight)
        inhibit_occ_pairs = subgraph.get(               # (occ_a, occ_b, magnitude)
            "inhibit_occ_pairs", []
        )

        if not nodes:
            return []

        # Index nodes
        idx_map: Dict[str, int] = {occ_id: i for i, occ_id in enumerate(nodes)}
        n = len(idx_map)

        if _HAS_GRAPHBLAS:
            return self._run_graphblas(
                nodes, edges, inhibit_occ_pairs, idx_map, n,
                seed_occurrence_ids, top_k,
            )
        else:
            return self._run_numpy(
                nodes, edges, inhibit_occ_pairs, idx_map, n,
                seed_occurrence_ids, top_k,
            )

    # ── GraphBLAS backend ────────────────────────────────────────────

    def _run_graphblas(
        self, nodes, edges, inhibit_occ_pairs, idx_map, n,
        seeds, top_k,
    ) -> List[BagOfEvidence]:
        import graphblas as gb
        from graphblas import Matrix, Vector, Scalar

        # Build adjacency matrix A (pull + precedes edges)
        A = Matrix.new(float, nrows=n, ncols=n)
        for src_occ, op, tgt_occ, weight in edges:
            if src_occ in idx_map and tgt_occ in idx_map:
                i, j = idx_map[src_occ], idx_map[tgt_occ]
                attention = nodes[src_occ]["attention_weight"]
                A[i, j] = weight * attention

        # Build inhibition matrix H from occurrence-level anti-correlation pairs.
        # Each (occ_a, occ_b, magnitude) entry from retrieval.load_subgraph()
        # represents two nodes whose SVD vectors are anti-correlated; they
        # suppress each other's activation symmetrically.
        H = Matrix.new(float, nrows=n, ncols=n)
        for occ_a, occ_b, magnitude in inhibit_occ_pairs:
            if occ_a in idx_map and occ_b in idx_map:
                i, j = idx_map[occ_a], idx_map[occ_b]
                scaled = magnitude * self.inhibit_scale
                # Symmetric — each node inhibits the other
                try:
                    current_ij = float(H.get(i, j, default=0.0))
                    if scaled > current_ij:
                        H[i, j] = scaled
                    current_ji = float(H.get(j, i, default=0.0))
                    if scaled > current_ji:
                        H[j, i] = scaled
                except Exception:
                    H[i, j] = scaled
                    H[j, i] = scaled

        # Seed activation vector
        h = Vector.new(float, size=n)
        seed_indices = [idx_map[s] for s in seeds if s in idx_map]
        for si in seed_indices:
            h[si] = 1.0

        # Mask to prevent seeds from receiving back-propagated energy
        mask = Vector.new(bool, size=n)
        for si in seed_indices:
            mask[si] = True

        # Update loop: h_{t+1} = α·h_t + A·h_t - H·h_t
        for _ in range(self.hop_limit):
            Ah = A.mxv(h)
            Hh = H.mxv(h)
            h_decay = h.dup()
            h_decay(mask, replace=True) << h_decay  # keep seed values decayed only

            h_next = Vector.new(float, size=n)
            h_next(~mask) << self.decay * h + Ah - Hh
            # Seeds only decay
            for si in seed_indices:
                try:
                    h_next[si] = self.decay * float(h[si])
                except Exception:
                    h_next[si] = 0.0
            h = h_next

        # Extract activations
        activations = {}
        for occ_id, i in idx_map.items():
            try:
                v = float(h[i])
            except Exception:
                v = 0.0
            activations[occ_id] = v

        return self._build_boe(activations, nodes, top_k)

    # ── NumPy fallback backend ───────────────────────────────────────

    def _run_numpy(
        self, nodes, edges, inhibit_occ_pairs, idx_map, n,
        seeds, top_k,
    ) -> List[BagOfEvidence]:
        # Build dense A
        A = np.zeros((n, n), dtype=float)
        for src_occ, op, tgt_occ, weight in edges:
            if src_occ in idx_map and tgt_occ in idx_map:
                i, j = idx_map[src_occ], idx_map[tgt_occ]
                attention = nodes[src_occ]["attention_weight"]
                A[i, j] = weight * attention

        # Build inhibition matrix H from occurrence-level anti-correlation pairs.
        H = np.zeros((n, n), dtype=float)
        for occ_a, occ_b, magnitude in inhibit_occ_pairs:
            if occ_a in idx_map and occ_b in idx_map:
                i, j = idx_map[occ_a], idx_map[occ_b]
                scaled = magnitude * self.inhibit_scale
                # Take element-wise maximum to handle duplicate pairs gracefully
                H[i, j] = max(H[i, j], scaled)
                H[j, i] = max(H[j, i], scaled)  # symmetric

        # Seed
        h = np.zeros(n, dtype=float)
        seed_indices = [idx_map[s] for s in seeds if s in idx_map]
        for si in seed_indices:
            h[si] = 1.0

        # Mask: seed indices are excluded from receiving back-prop
        mask = np.zeros(n, dtype=bool)
        for si in seed_indices:
            mask[si] = True

        # Update loop: h_{t+1} = α·h + A·h - H·h  (masked)
        for _ in range(self.hop_limit):
            h_next = self.decay * h + A @ h - H @ h
            # Restore seeds to decay-only (no back-prop energy)
            h_next[mask] = self.decay * h[mask]
            # Clip to [0, 1]
            h_next = np.clip(h_next, 0.0, 1.0)
            h = h_next

        activations = {occ_id: float(h[i]) for occ_id, i in idx_map.items()}
        return self._build_boe(activations, nodes, top_k)

    # ── Shared output builder ────────────────────────────────────────

    def _build_boe(
        self,
        activations: Dict[str, float],
        nodes: dict,
        top_k: int,
    ) -> List[BagOfEvidence]:
        results = []
        for occ_id, activation in activations.items():
            if activation <= 0.0:
                continue
            node = nodes[occ_id]
            results.append(BagOfEvidence(
                occurrence_id=occ_id,
                activation=activation,
                hunk_id=node["hunk_id"],
                node_kind=node["node_kind"],
                attention_weight=node["attention_weight"],
                static_mass=node["static_mass"],
            ))

        results.sort(key=lambda x: -x.activation)
        return results[:top_k]
