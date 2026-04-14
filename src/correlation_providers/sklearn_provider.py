"""
Sklearn-based correlation provider — TF-IDF + DBSCAN clustering.
No external model downloads needed.
"""
from sklearn.cluster import DBSCAN
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict

from .base import CorrelationProvider


class SklearnCorrelationProvider(CorrelationProvider):
    """Cluster trending terms using TF-IDF character n-grams + DBSCAN."""

    def __init__(self, **kwargs):
        print("Initializing correlation engine (TF-IDF + DBSCAN)...")
        self.vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(2, 4),
            min_df=1,
            sublinear_tf=True,
        )
        print("Correlation engine ready!")

    @property
    def name(self) -> str:
        return "sklearn (TF-IDF + DBSCAN)"

    def analyze_trends(self, trends: List[Dict],
                       min_cluster_size: int = 2) -> Dict:
        terms = [t['term'] for t in trends]

        print("Generating TF-IDF embeddings...")
        embeddings = self.vectorizer.fit_transform(terms).toarray()

        print("Clustering terms...")
        clustering = DBSCAN(eps=0.9, min_samples=min_cluster_size, metric='cosine')
        labels = clustering.fit_predict(embeddings)

        clusters = self._organize_clusters(terms, labels, embeddings)
        unified_topic = self._generate_unified_topic(clusters, terms, embeddings)

        return {
            'clusters': clusters,
            'unified_topic': unified_topic,
            'total_terms': len(terms),
            'num_clusters': len([c for c in clusters if c['label'] != 'noise']),
        }

    # ------------------------------------------------------------------
    # Internal helpers (moved verbatim from correlation_engine.py)
    # ------------------------------------------------------------------

    def _organize_clusters(self, terms: List[str], labels: np.ndarray,
                           embeddings: np.ndarray) -> List[Dict]:
        clusters = []
        unique_labels = set(labels)

        for label in unique_labels:
            if label == -1:
                cluster_terms = [terms[i] for i in range(len(terms)) if labels[i] == label]
                clusters.append({
                    'label': 'noise',
                    'terms': cluster_terms,
                    'size': len(cluster_terms),
                    'confidence': 0.0,
                })
            else:
                indices = [i for i in range(len(terms)) if labels[i] == label]
                cluster_terms = [terms[i] for i in indices]
                cluster_embeddings = embeddings[indices]

                if len(cluster_embeddings) > 1:
                    similarities = cosine_similarity(cluster_embeddings)
                    mask = np.ones_like(similarities) - np.eye(len(similarities))
                    confidence = (similarities * mask).sum() / mask.sum()
                else:
                    confidence = 0.5

                clusters.append({
                    'label': f'cluster_{label + 1}',
                    'terms': cluster_terms,
                    'size': len(cluster_terms),
                    'confidence': float(confidence),
                })

        clusters.sort(key=lambda x: x['size'], reverse=True)
        return clusters

    def _generate_unified_topic(self, clusters: List[Dict], all_terms: List[str],
                                embeddings: np.ndarray) -> Dict:
        valid_clusters = [c for c in clusters if c['label'] != 'noise' and c['size'] >= 2]

        if not valid_clusters:
            return {
                'theme': 'Current Events and Emerging Trends',
                'description': 'A collection of diverse trending topics',
                'confidence': 0.5,
            }

        top_clusters = valid_clusters[:3]

        key_terms = []
        for cluster in top_clusters:
            key_terms.extend(cluster['terms'][:2])

        theme = self._create_theme_from_terms(key_terms)

        total_size = sum(c['size'] for c in top_clusters)
        confidence = sum(c['confidence'] * c['size'] for c in top_clusters) / total_size

        return {
            'theme': theme,
            'key_terms': key_terms,
            'description': f'Connecting {len(top_clusters)} major trend clusters',
            'confidence': float(confidence),
        }

    @staticmethod
    def _create_theme_from_terms(terms: List[str]) -> str:
        tech_keywords = ['ai', 'artificial', 'technology', 'digital', 'computing', 'cyber', 'quantum']
        env_keywords = ['climate', 'environment', 'sustainable', 'renewable', 'carbon', 'ocean']
        social_keywords = ['social', 'mental', 'health', 'inequality', 'privacy', 'work']
        science_keywords = ['space', 'gene', 'medicine', 'quantum', 'research']

        categories = {
            'Technology': sum(1 for t in terms for kw in tech_keywords if kw in t.lower()),
            'Environment': sum(1 for t in terms for kw in env_keywords if kw in t.lower()),
            'Society': sum(1 for t in terms for kw in social_keywords if kw in t.lower()),
            'Science': sum(1 for t in terms for kw in science_keywords if kw in t.lower()),
        }

        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        top_cats = [cat for cat, count in sorted_cats[:2] if count > 0]

        if len(top_cats) >= 2:
            return f"{top_cats[0]} and {top_cats[1]} Trends"
        elif len(top_cats) == 1:
            return f"{top_cats[0]} and Innovation"
        else:
            return "Emerging Global Trends"
