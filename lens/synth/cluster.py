"""Cluster the annotators' `other` patterns (BUILD_PLAN 8.2) into taxonomy proposals for gate G4.

Each `other` event's "proposed_name: description" is embedded with a local sentence-transformer
(config `synth.cluster.model`, pinned revision, CPU, mean pooling) and grouped by average-link
agglomerative clustering on cosine similarity. Each cluster is compared with the existing taxonomy
patterns' names, so close ones are suggested as merges.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable, Mapping, Sequence

import numpy as np

from lens.schemas.config import Cluster
from lens.schemas.corpus import Proposal

Embed = Callable[[Sequence[str]], np.ndarray]


def minilm(cfg: Cluster) -> Embed:
    """Normalized mean-pooled embeddings from the configured model (downloaded once, then cached)."""
    import torch
    from transformers import AutoModel, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(cfg.model, revision=cfg.revision)
    model = AutoModel.from_pretrained(cfg.model, revision=cfg.revision).eval()

    def embed(texts: Sequence[str]) -> np.ndarray:
        out = []
        with torch.no_grad():
            for i in range(0, len(texts), 32):
                batch = tok(
                    list(texts[i : i + 32]),
                    padding=True,
                    truncation=True,
                    max_length=128,
                    return_tensors="pt",
                )
                h = model(**batch).last_hidden_state
                m = batch["attention_mask"].unsqueeze(-1).float()
                v = (h * m).sum(1) / m.sum(1).clamp(min=1e-9)
                out.append(torch.nn.functional.normalize(v, dim=1).numpy())
        return np.concatenate(out) if out else np.zeros((0, 1))

    return embed


def average_link(sim: np.ndarray, threshold: float) -> list[list[int]]:
    """Agglomerative clustering: merge the two most similar clusters (mean pairwise cosine) while that
    similarity is at least `threshold`. Cluster similarities are updated in place (Lance-Williams for
    average linkage), so each merge costs O(n). Deterministic; clusters ordered by size, then first
    member."""
    n = sim.shape[0]
    clusters: dict[int, list[int]] = {i: [i] for i in range(n)}
    s = sim.astype(float).copy()
    np.fill_diagonal(s, -np.inf)
    alive = np.ones(n, dtype=bool)
    while alive.sum() > 1:
        m = np.where(alive[:, None] & alive[None, :], s, -np.inf)
        flat = int(np.argmax(m))
        a, b = divmod(flat, n)
        if m[a, b] < threshold:
            break
        a, b = min(a, b), max(a, b)
        na, nb = len(clusters[a]), len(clusters[b])
        merged = (na * s[a] + nb * s[b]) / (na + nb)
        s[a], s[:, a] = merged, merged
        s[a, a] = -np.inf
        alive[b] = False
        s[b], s[:, b] = -np.inf, -np.inf
        clusters[a] = sorted(clusters[a] + clusters.pop(b))
    return sorted(clusters.values(), key=lambda c: (-len(c), c[0]))


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s or "pattern"


def propose(
    items: Sequence[tuple[str, str, str]],  # (<video>/<event>, proposed name, description)
    patterns: Sequence[str],
    cfg: Cluster,
    embed: Embed,
    brand_of: Mapping[str, str | None] | None = None,  # video -> brand; None = own video (not counted)
) -> tuple[list[Proposal], int]:
    """Proposals for clusters with at least `cfg.min_members` members from `cfg.min_brands` brands (our own
    videos do not count), and the number of events left out."""
    if not items:
        return [], 0
    texts = [f"{name}: {desc}" for _, name, desc in items]
    vec = embed(texts)
    sim = vec @ vec.T
    known = embed([p.replace("_", " ") for p in patterns]) if patterns else np.zeros((0, vec.shape[1]))
    proposals: list[Proposal] = []
    left = 0
    taken: set[str] = set(patterns)
    for members in average_link(sim, cfg.threshold):
        vids = {items[i][0].split("/")[0] for i in members}
        brands: set[str | None] = {brand_of.get(v, v) for v in vids} if brand_of is not None else set(vids)
        brands.discard(None)
        if len(members) < cfg.min_members or len(brands) < cfg.min_brands:
            left += len(members)
            continue
        names = Counter(items[i][1].strip().lower() for i in members)
        top = sorted(names.items(), key=lambda kv: (-kv[1], kv[0]))
        name = top[0][0]
        pid = slug(name)
        while pid in taken:
            pid += "_2"
        taken.add(pid)
        centre = vec[members].mean(0)
        centre /= np.linalg.norm(centre) or 1.0
        nearest, similarity = None, 0.0
        if len(known):
            sims = known @ centre
            j = int(sims.argmax())
            nearest, similarity = patterns[j], round(float(sims[j]), 3)
        ids = [items[i][0] for i in members]
        proposals.append(
            Proposal(
                id=pid,
                name=name,
                members=ids,
                videos=len({m.split("/")[0] for m in ids}),
                names=[n for n, _ in top],
                nearest_pattern=nearest,
                similarity=similarity,
                suggestion=f"merge:{nearest}" if nearest and similarity >= cfg.merge_similarity else "new",
            )
        )
    return proposals, left
