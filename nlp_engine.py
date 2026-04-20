"""
NLP & ML Engine for Breaking News Finder
- TF-IDF vectorization for text similarity
- Cosine similarity for duplicate/similar content detection
- Keyword extraction and n-gram analysis
- Coverage gap analysis between competitors
- Optimized for large datasets with chunked processing
"""

import re
import logging
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import DBSCAN

from config import (
    MIN_SIMILARITY_THRESHOLD,
    HIGH_SIMILARITY_THRESHOLD,
    TOP_KEYWORDS_COUNT,
    NGRAM_RANGE,
    CHUNK_SIZE,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────
# Text Preprocessing
# ──────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Clean and normalize text for NLP processing."""
    if not text:
        return ""
    # Remove URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove special characters but keep Gujarati unicode and basic punctuation
    text = re.sub(r"[^\w\s\u0A80-\u0AFF.,!?-]", " ", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def combine_article_text(article: Dict) -> str:
    """Combine title and keywords into a single text representation."""
    parts = []
    if article.get("title"):
        parts.append(article["title"])
    if article.get("keywords"):
        parts.append(article["keywords"])
    return clean_text(" ".join(parts))


# ──────────────────────────────────────────────────────────
# TF-IDF & Similarity Engine
# ──────────────────────────────────────────────────────────

class NewsAnalyzer:
    """Core NLP analysis engine with optimized large-dataset handling."""

    def __init__(self, articles: List[Dict]):
        self.articles = articles
        self.df = pd.DataFrame(articles) if articles else pd.DataFrame()
        self.tfidf_matrix = None
        self.vectorizer = None
        self.similarity_matrix = None
        self._prepared = False

    def prepare(self):
        """Prepare text data and build TF-IDF matrix."""
        if self.df.empty:
            logger.warning("No articles to analyze")
            return

        # Create combined text column
        self.df["combined_text"] = self.df.apply(
            lambda row: combine_article_text(row.to_dict()), axis=1
        )

        # Filter out empty texts
        valid_mask = self.df["combined_text"].str.len() > 0
        self.df = self.df[valid_mask].reset_index(drop=True)

        if self.df.empty:
            logger.warning("No valid text data after cleaning")
            return

        # Build TF-IDF matrix with n-grams
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=NGRAM_RANGE,
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,
        )

        texts = self.df["combined_text"].tolist()
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        self._prepared = True
        logger.info(f"TF-IDF matrix built: {self.tfidf_matrix.shape}")

    def compute_similarity_matrix(self) -> Optional[np.ndarray]:
        """Compute pairwise cosine similarity with chunked processing for large datasets."""
        if not self._prepared or self.tfidf_matrix is None:
            return None

        n = self.tfidf_matrix.shape[0]

        if n <= CHUNK_SIZE:
            # Small dataset: compute directly
            similarity = cosine_similarity(self.tfidf_matrix)
            # Ensure values are in valid range [0, 1] to prevent negative values
            self.similarity_matrix = np.clip(similarity, 0.0, 1.0)
        else:
            # Large dataset: compute in chunks to save memory
            logger.info(f"Computing similarity in chunks (n={n})...")
            self.similarity_matrix = np.zeros((n, n), dtype=np.float32)
            for i in range(0, n, CHUNK_SIZE):
                end_i = min(i + CHUNK_SIZE, n)
                for j in range(i, n, CHUNK_SIZE):
                    end_j = min(j + CHUNK_SIZE, n)
                    chunk_sim = cosine_similarity(
                        self.tfidf_matrix[i:end_i],
                        self.tfidf_matrix[j:end_j]
                    )
                    # Ensure values are in valid range [0, 1]
                    chunk_sim = np.clip(chunk_sim, 0.0, 1.0)
                    self.similarity_matrix[i:end_i, j:end_j] = chunk_sim
                    if i != j:
                        self.similarity_matrix[j:end_j, i:end_i] = chunk_sim.T

        return self.similarity_matrix

    # ──────────────────────────────────────────────────────
    # Similar Content Detection
    # ──────────────────────────────────────────────────────

    def find_similar_articles(self) -> List[Dict]:
        """
        Find pairs of similar articles across different competitors.
        Returns list of similar article pairs with similarity scores.
        Optimized with vectorized operations.
        """
        if self.similarity_matrix is None:
            self.compute_similarity_matrix()

        if self.similarity_matrix is None:
            return []

        n = len(self.df)
        sources = self.df["source"].values
        
        triu_indices = np.triu_indices(n, k=1)
        valid_mask = sources[triu_indices[0]] != sources[triu_indices[1]]
        
        row_indices = triu_indices[0][valid_mask]
        col_indices = triu_indices[1][valid_mask]
        sim_scores = self.similarity_matrix[row_indices, col_indices]
        
        high_sim_mask = sim_scores >= MIN_SIMILARITY_THRESHOLD
        high_sim_scores = sim_scores[high_sim_mask]
        high_row_indices = row_indices[high_sim_mask]
        high_col_indices = col_indices[high_sim_mask]
        
        similar_pairs = []
        for idx in range(len(high_sim_scores)):
            i, j = high_row_indices[idx], high_col_indices[idx]
            sim_score = high_sim_scores[idx]
            
            pair = {
                "article_1": {
                    "source": self.df.iloc[i]["source"],
                    "title": self.df.iloc[i]["title"],
                    "url": self.df.iloc[i]["url"],
                    "published_at": self.df.iloc[i].get("published_at", ""),
                },
                "article_2": {
                    "source": self.df.iloc[j]["source"],
                    "title": self.df.iloc[j]["title"],
                    "url": self.df.iloc[j]["url"],
                    "published_at": self.df.iloc[j].get("published_at", ""),
                },
                "similarity_score": round(float(sim_score), 4),
                "is_likely_duplicate": sim_score >= HIGH_SIMILARITY_THRESHOLD,
            }
            similar_pairs.append(pair)

        similar_pairs.sort(key=lambda x: x["similarity_score"], reverse=True)
        logger.info(f"Found {len(similar_pairs)} similar article pairs")
        return similar_pairs

    # ──────────────────────────────────────────────────────
    # Topic Clustering with DBSCAN
    # ──────────────────────────────────────────────────────

    def cluster_topics(self, eps: float = 0.5, min_samples: int = 2) -> Dict:
        """Cluster articles into topics using DBSCAN on TF-IDF features."""
        if not self._prepared or self.tfidf_matrix is None:
            return {}
        
        try:
            similarity = cosine_similarity(self.tfidf_matrix)
            distance_matrix = 1 - similarity
            distance_matrix = np.clip(distance_matrix, 0.0, 1.0)
            np.fill_diagonal(distance_matrix, 0)

            clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
            labels = clustering.fit_predict(distance_matrix)
        except Exception as e:
            logger.warning(f"Clustering failed: {e}")
            return {}

        self.df["cluster"] = labels

        clusters = {}
        for label in set(labels):
            if label == -1:
                continue  # Skip noise
            cluster_df = self.df[self.df["cluster"] == label]
            sources_in_cluster = cluster_df["source"].unique().tolist()

            # Get representative keywords for the cluster
            cluster_texts = cluster_df["combined_text"].tolist()
            cluster_keywords = self._extract_keywords_from_texts(cluster_texts, top_n=10)

            clusters[int(label)] = {
                "article_count": len(cluster_df),
                "sources": sources_in_cluster,
                "source_count": len(sources_in_cluster),
                "articles": cluster_df[["source", "title", "url", "published_at"]].to_dict("records"),
                "top_keywords": cluster_keywords,
            }

        logger.info(f"Found {len(clusters)} topic clusters")
        return clusters

    # ──────────────────────────────────────────────────────
    # Keyword & N-gram Analysis
    # ──────────────────────────────────────────────────────

    def extract_top_keywords(self, source: Optional[str] = None) -> List[Tuple[str, float]]:
        """Extract top keywords/n-grams using TF-IDF scores."""
        if not self._prepared or self.vectorizer is None:
            return []

        if source:
            mask = self.df["source"] == source
            if not mask.any():
                return []
            matrix = self.tfidf_matrix[mask.values]
        else:
            matrix = self.tfidf_matrix

        # Mean TF-IDF scores across documents
        mean_scores = np.array(matrix.mean(axis=0)).flatten()
        feature_names = self.vectorizer.get_feature_names_out()

        # Get top keywords
        top_indices = mean_scores.argsort()[-TOP_KEYWORDS_COUNT:][::-1]
        keywords = [(feature_names[i], round(float(mean_scores[i]), 4)) for i in top_indices]

        return keywords

    def _extract_keywords_from_texts(self, texts: List[str], top_n: int = 10) -> List[str]:
        """Extract keywords from a subset of texts."""
        if not texts:
            return []

        # Use word frequency as a simpler method for subsets
        all_words = " ".join(texts).split()
        counter = Counter(all_words)
        # Filter out single characters and very common words
        filtered = [(w, c) for w, c in counter.most_common(top_n * 3) if len(w) > 2]
        return [w for w, c in filtered[:top_n]]

    def keyword_comparison(self) -> Dict[str, List[Tuple[str, float]]]:
        """Compare top keywords across all competitors."""
        comparison = {}
        for source in self.df["source"].unique():
            comparison[source] = self.extract_top_keywords(source)
        return comparison

    # ──────────────────────────────────────────────────────
    # Coverage Gap Analysis
    # ──────────────────────────────────────────────────────

    def coverage_gap_analysis(self) -> Dict:
        """
        Analyze content gaps: which topics are covered by some competitors
        but missed by others.
        """
        if not self._prepared:
            return {}

        sources = self.df["source"].unique().tolist()
        if len(sources) < 2:
            return {}

        # Get keyword sets per source
        source_keywords = {}
        for source in sources:
            kws = self.extract_top_keywords(source)
            source_keywords[source] = set(kw for kw, score in kws)

        # Find unique keywords per source (covered by them but not others)
        gaps = {}
        for source in sources:
            other_keywords = set()
            for other_source in sources:
                if other_source != source:
                    other_keywords.update(source_keywords.get(other_source, set()))

            unique_to_source = source_keywords.get(source, set()) - other_keywords
            missed_by_source = other_keywords - source_keywords.get(source, set())

            gaps[source] = {
                "unique_keywords": list(unique_to_source)[:15],
                "missed_keywords": list(missed_by_source)[:15],
                "total_keywords": len(source_keywords.get(source, set())),
            }

        return gaps

    # ──────────────────────────────────────────────────────
    # Who Published First Analysis
    # ──────────────────────────────────────────────────────

    def first_publisher_analysis(self) -> List[Dict]:
        """
        For similar article pairs, determine who published first.
        Returns analysis of which competitor breaks news first.
        """
        similar_pairs = self.find_similar_articles()
        first_publisher_stats = Counter()
        detailed_results = []

        for pair in similar_pairs:
            a1 = pair["article_1"]
            a2 = pair["article_2"]

            if a1.get("published_at") and a2.get("published_at"):
                try:
                    dt1 = pd.to_datetime(a1["published_at"])
                    dt2 = pd.to_datetime(a2["published_at"])

                    if dt1 < dt2:
                        first = a1["source"]
                        second = a2["source"]
                        time_diff = (dt2 - dt1).total_seconds() / 60  # minutes
                    else:
                        first = a2["source"]
                        second = a1["source"]
                        time_diff = (dt1 - dt2).total_seconds() / 60

                    first_publisher_stats[first] += 1
                    detailed_results.append({
                        "topic": a1["title"][:100],
                        "first_publisher": first,
                        "second_publisher": second,
                        "time_gap_minutes": round(time_diff, 1),
                        "similarity": pair["similarity_score"],
                    })
                except Exception:
                    pass

        return {
            "stats": dict(first_publisher_stats.most_common()),
            "details": sorted(detailed_results, key=lambda x: x["similarity"], reverse=True),
        }

    # ──────────────────────────────────────────────────────
    # Summary Statistics
    # ──────────────────────────────────────────────────────

    def generate_summary(self) -> Dict:
        """Generate overall analysis summary."""
        if self.df.empty:
            return {"total_articles": 0}

        source_counts = self.df["source"].value_counts().to_dict()
        total = len(self.df)

        return {
            "total_articles": total,
            "articles_per_source": source_counts,
            "sources_count": len(source_counts),
            "has_timestamps": int(self.df["published_at"].astype(bool).sum()),
            "has_keywords": int(self.df["keywords"].astype(bool).sum()),
        }


def run_full_analysis(articles: List[Dict]) -> Dict:
    """
    Run the complete NLP analysis pipeline.
    Returns a comprehensive analysis dictionary.
    """
    analyzer = NewsAnalyzer(articles)
    analyzer.prepare()

    logger.info("Running full analysis pipeline...")

    results = {
        "summary": analyzer.generate_summary(),
        "similar_articles": analyzer.find_similar_articles(),
        "topic_clusters": analyzer.cluster_topics(),
        "keyword_comparison": {
            source: [(kw, score) for kw, score in kws]
            for source, kws in analyzer.keyword_comparison().items()
        },
        "coverage_gaps": analyzer.coverage_gap_analysis(),
        "first_publisher": analyzer.first_publisher_analysis(),
    }

    logger.info("Analysis complete!")
    return results
