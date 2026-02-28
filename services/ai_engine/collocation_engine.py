"""
CareerTrojan — Collocation Engine
=================================
Extracts multi-word concepts and proximity/negation patterns from text.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z\-']+")
NEGATION_WORDS = {"not", "no", "never", "nor", "without", "neither", "n't"}


@dataclass
class CollocationResult:
    phrase: str
    score: float
    frequency: int


class CollocationEngine:
    def __init__(self, min_freq: int = 2, pmi_threshold: float = 2.0, window_size: int = 5):
        self.min_freq = max(1, min_freq)
        self.pmi_threshold = pmi_threshold
        self.window_size = max(2, window_size)

    def _tokenize(self, text: str) -> List[str]:
        return [match.group(0).lower() for match in TOKEN_RE.finditer(text or "")]

    def _all_tokens(self, texts: Sequence[str]) -> List[List[str]]:
        return [self._tokenize(text) for text in texts if text]

    def extract_ngrams(self, texts: Sequence[str], n: int = 2) -> Counter:
        n = max(1, n)
        counts = Counter()
        for tokens in self._all_tokens(texts):
            if len(tokens) < n:
                continue
            for index in range(len(tokens) - n + 1):
                ngram = tuple(tokens[index:index + n])
                counts[ngram] += 1
        return counts

    def extract_pmi_collocations(self, texts: Sequence[str], n: int = 2, top_k: int = 200) -> List[CollocationResult]:
        tokenized = self._all_tokens(texts)
        unigram_counts = Counter()
        for tokens in tokenized:
            unigram_counts.update(tokens)

        ngram_counts = self.extract_ngrams(texts, n=n)
        total_unigrams = sum(unigram_counts.values())
        total_ngrams = sum(ngram_counts.values())
        if total_unigrams == 0 or total_ngrams == 0:
            return []

        results: List[CollocationResult] = []
        for ngram, frequency in ngram_counts.items():
            if frequency < self.min_freq:
                continue

            p_ngram = frequency / total_ngrams
            p_parts = 1.0
            for token in ngram:
                p_parts *= unigram_counts[token] / total_unigrams
            if p_parts <= 0:
                continue

            pmi = math.log2(p_ngram / p_parts)
            if pmi >= self.pmi_threshold:
                results.append(
                    CollocationResult(
                        phrase=" ".join(ngram),
                        score=round(float(pmi), 4),
                        frequency=int(frequency),
                    )
                )

        results.sort(key=lambda item: (item.score, item.frequency), reverse=True)
        return results[:top_k]

    def find_near_pairs(
        self,
        texts: Sequence[str],
        window: int = 5,
        min_hits: int = 2,
        top_k: int = 100,
    ) -> Tuple[List[Dict[str, float]], List[Dict[str, int]]]:
        window = max(2, window)
        pair_hits = Counter()
        hit_details: List[Dict[str, int]] = []

        for text_index, tokens in enumerate(self._all_tokens(texts)):
            for left_index, left_token in enumerate(tokens):
                right_limit = min(len(tokens), left_index + window + 1)
                for right_index in range(left_index + 1, right_limit):
                    right_token = tokens[right_index]
                    if left_token == right_token:
                        continue
                    pair = tuple(sorted((left_token, right_token)))
                    pair_hits[pair] += 1
                    hit_details.append(
                        {
                            "text_index": text_index,
                            "left_index": left_index,
                            "right_index": right_index,
                            "distance": right_index - left_index,
                        }
                    )

        ranked = [
            {"pair": f"{a} ~ {b}", "hits": int(count)}
            for (a, b), count in pair_hits.items()
            if count >= min_hits
        ]
        ranked.sort(key=lambda item: item["hits"], reverse=True)
        return ranked[:top_k], hit_details

    def tag_negations(self, texts: Sequence[str], span_window: int = 4) -> Dict[str, List[Tuple[int, int]]]:
        span_window = max(1, span_window)
        tags: Dict[str, List[Tuple[int, int]]] = defaultdict(list)

        for text_idx, tokens in enumerate(self._all_tokens(texts)):
            for idx, token in enumerate(tokens):
                if token not in NEGATION_WORDS:
                    continue
                end = min(len(tokens), idx + span_window + 1)
                phrase_tokens = tokens[idx + 1:end]
                if not phrase_tokens:
                    continue
                phrase = " ".join(phrase_tokens)
                tags[phrase].append((text_idx, idx))

        return dict(tags)

    def extract_phrase_spans(
        self,
        texts: Sequence[str],
        min_len: int = 2,
        max_len: int = 3,
    ) -> Dict[str, List[Tuple[int, int, int]]]:
        min_len = max(1, min_len)
        max_len = max(min_len, max_len)
        spans: Dict[str, List[Tuple[int, int, int]]] = defaultdict(list)

        for text_index, tokens in enumerate(self._all_tokens(texts)):
            for n in range(min_len, max_len + 1):
                if len(tokens) < n:
                    continue
                for start in range(0, len(tokens) - n + 1):
                    end = start + n
                    phrase = " ".join(tokens[start:end])
                    spans[phrase].append((text_index, start, end))

        return {phrase: positions for phrase, positions in spans.items() if len(positions) >= self.min_freq}
