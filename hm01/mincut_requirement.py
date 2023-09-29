from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import math

from hm01.clusterers.abstract_clusterer import AbstractClusterer
from hm01.clusterers.ikc_wrapper import IkcClusterer


@dataclass
class MincutRequirement:
    """ A linear combination of the log10 cluster size, mcd of the cluster, and the k given in the input 

    (VR) These store the coefficients of the terms of the mincut requirement

    Ex.
        log10 = 4
        mcd = 2
        k = 0.4
        constant = 1

        -> 4log10n + 2mcd(c) + 0.4k + 1
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
        """ (VR) Compute the threshold of a given clusterer """
        log10 = math.log10(cluster.n()) if cluster.n() > 0 else 0
        mcd = cluster.mcd() if mcd_override is None else mcd_override
        k = clusterer.k if isinstance(clusterer, IkcClusterer) else 0           # (VR) k is dependent on the clusterer being IKC
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
        s = s.replace(" ", "")                                                  # (VR) Remove spaces from the input string

        def take_num(st):
            """ (VR) Split coefficient and term in linear combination
            
            Returns: coefficient and rest of the string (tuple[float, str])
            """
            i = 0
            buf = []
            if not st or not st[i].isdigit():
                raise ValueError(f"Expected a number, got {st[i]}")
            while i < len(st) and (st[i].isdigit() or st[i] == "."):
                buf.append(st[i])
                i += 1
            return float("".join(buf)), st[i:]

        def one_of(words, s):
            """ (VR) Grab term from the string
            
            Returns: One of [log10, mcd, k] and the rest of the string (tuple[str, str])
            """
            for word in words:
                if s.startswith(word):
                    return word, s[len(word) :]
            raise ValueError(f"Expected one of {words}, got {s}")

        # (VR) Initialize values and dictionary of unpacked terms and coefficients
        log10 = 0
        mcd = 0
        k = 0
        constant = 0
        vals = {}
        while s:
            n, s = take_num(s)                                  # (VR) Fetch the next number in the string
            if s and s[0] == "+":                               # (VR) If there is a plus next then the number is a constant
                constant += n
                s = s[1:]
                continue
            if not s:                                           # (VR) If we're at the end of the string, then we also have a constant
                constant += n
                break
            key, s = one_of(["log10", "mcd", "k"], s)           # (VR) Otherwise, the number is a coefficient of a term
            vals[key] = float(n)                                
            if s and s[0] == "+":                               # (VR) Move to the next term after the plus
                s = s[1:]
        if "log10" in vals:
            log10 = vals["log10"]
        if "mcd" in vals:
            mcd = vals["mcd"]
        if "k" in vals:
            k = vals["k"]
        return MincutRequirement(log10, mcd, k, int(constant))
