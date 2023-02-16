from __future__ import annotations
from dataclasses import dataclass
import math
from hm01.clusterers.abstract_clusterer import AbstractClusterer
from .clusterers.leiden_wrapper import LeidenClusterer
from .clusterers.ikc_wrapper import IkcClusterer
from typing import List, Optional, Tuple, Union, Dict, Deque


@dataclass
class MincutRequirement:
    """A linear combination of the log10 cluster size, mcd of the cluster, and the k given in the input
    """

    log10: float
    mcd: float
    k: float
    constant: int

    def is_sane(self, clusterer: AbstractClusterer):
        """Check if the mincut requirement is reasonable"""
        if self.log10 <= 0 and self.mcd <= 0 and self.k <= 0 and self.constant <= 0:
            return False
        if not isinstance(clusterer, IkcClusterer):
            return self.k == 0
        return True

    def validity_threshold(
        self, clusterer: AbstractClusterer, cluster, mcd_override: Optional[int] = None
    ) -> float:
        # TODO: mcd_override is kind of a hack
        log10 = math.log10(cluster.n()) if cluster.n() > 0 else 0
        mcd = cluster.mcd() if mcd_override is None else mcd_override
        k = clusterer.k if isinstance(clusterer, IkcClusterer) else 0
        return self.log10 * log10 + self.mcd * mcd + self.k * k + self.constant

    @staticmethod
    def most_stringent() -> MincutRequirement:
        return MincutRequirement(0, 0, 0, 2)

    @staticmethod
    def from_constant(n: int) -> MincutRequirement:
        return MincutRequirement(0, 0, 0, n)

    @staticmethod
    def try_from_str(s):
        """Parse a mincut requirement from a string (given in the CLI)"""
        s = s.replace(" ", "")

        def take_num(st):
            i = 0
            buf = []
            if not st or not st[i].isdigit():
                raise ValueError(f"Expected a number, got {st[i]}")
            while i < len(st) and (st[i].isdigit() or st[i] == "."):
                buf.append(st[i])
                i += 1
            return float("".join(buf)), st[i:]

        def one_of(words, s):
            for word in words:
                if s.startswith(word):
                    return word, s[len(word) :]
            raise ValueError(f"Expected one of {words}, got {s}")

        log10 = 0
        mcd = 0
        k = 0
        constant = 0
        vals = {}
        while s:
            n, s = take_num(s)
            if s and s[0] == "+":
                constant += n
                s = s[1:]
                continue
            if not s:
                constant += n
                break
            key, s = one_of(["log10", "mcd", "k"], s)
            vals[key] = float(n)
            if s and s[0] == "+":
                s = s[1:]
        if "log10" in vals:
            log10 = vals["log10"]
        if "mcd" in vals:
            mcd = vals["mcd"]
        if "k" in vals:
            k = vals["k"]
        return MincutRequirement(log10, mcd, k, int(constant))
