"""
Correlation Engine - analyzes trending terms and identifies unified topics
"""
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict, Tuple


class CorrelationEngine:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the correlation engine with a sentence transformer model
        
        Args:
            model_name: HuggingFace model for embeddings (default: lightweight MiniLM)
        """
        print(f"Loading NLP model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("Model loaded!")
    
    def analyze_trends(self, trends: List[Dict], min_cluster_size: int = 2) -> Dict:
        """
        Analyze trending terms and identify thematic clusters
        
        Args:
            trends: List of trend dictionaries from TrendScraper
            min_cluster_size: Minimum terms per cluster
        
        Returns:
            Dictionary with clusters and unified topic
        """
        # Extract just the terms
        terms = [t['term'] for t in trends]
        
        # Generate embeddings
        print("Generating embeddings...")
        embeddings = self.model.encode(terms)
        
        # Cluster using DBSCAN
        print("Clustering terms...")
        clustering = DBSCAN(eps=0.4, min_samples=min_cluster_size, metric='cosine')
        labels = clustering.fit_predict(embeddings)
        
        # Organize into clusters
        clusters = self._organize_clusters(terms, labels, embeddings)
        
        # Generate unified topic
        unified_topic = self._generate_unified_topic(clusters, terms, embeddings)
        
        return {
            'clusters': clusters,
            'unified_topic': unified_topic,
            'total_terms': len(terms),
            'num_clusters': len([c for c in clusters if c['label'] != 'noise'])
        }
    
    def _organize_clusters(self, terms: List[str], labels: np.ndarray, 
                          embeddings: np.ndarray) -> List[Dict]:
        """Group terms into clusters with confidence scores"""
        clusters = []
        unique_labels = set(labels)
        
        for label in unique_labels:
            if label == -1:
                # Noise cluster
                cluster_terms = [terms[i] for i in range(len(terms)) if labels[i] == label]
                clusters.append({
                    'label': 'noise',
                    'terms': cluster_terms,
                    'size': len(cluster_terms),
                    'confidence': 0.0
                })
            else:
                # Valid cluster
                indices = [i for i in range(len(terms)) if labels[i] == label]
                cluster_terms = [terms[i] for i in indices]
                cluster_embeddings = embeddings[indices]
                
                # Calculate cluster cohesion (average pairwise similarity)
                if len(cluster_embeddings) > 1:
                    similarities = cosine_similarity(cluster_embeddings)
                    # Average similarity excluding diagonal
                    mask = np.ones_like(similarities) - np.eye(len(similarities))
                    confidence = (similarities * mask).sum() / mask.sum()
                else:
                    confidence = 0.5
                
                clusters.append({
                    'label': f'cluster_{label + 1}',
                    'terms': cluster_terms,
                    'size': len(cluster_terms),
                    'confidence': float(confidence)
                })
        
        # Sort by size (largest first)
        clusters.sort(key=lambda x: x['size'], reverse=True)
        return clusters
    
    def _generate_unified_topic(self, clusters: List[Dict], all_terms: List[str],
                               embeddings: np.ndarray) -> Dict:
        """
        Generate a unified topic that connects the main clusters
        
        Uses a simple centroid-based approach to find the central theme
        """
        # Filter out noise and small clusters
        valid_clusters = [c for c in clusters if c['label'] != 'noise' and c['size'] >= 2]
        
        if not valid_clusters:
            # Fallback to most common themes
            return {
                'theme': 'Current Events and Emerging Trends',
                'description': 'A collection of diverse trending topics',
                'confidence': 0.5
            }
        
        # Get top 2-3 clusters
        top_clusters = valid_clusters[:3]
        
        # Extract representative terms
        key_terms = []
        for cluster in top_clusters:
            key_terms.extend(cluster['terms'][:2])  # Top 2 from each cluster
        
        # Simple theme generation based on cluster composition
        theme = self._create_theme_from_terms(key_terms)
        
        # Calculate confidence (weighted by cluster sizes)
        total_size = sum(c['size'] for c in top_clusters)
        confidence = sum(c['confidence'] * c['size'] for c in top_clusters) / total_size
        
        return {
            'theme': theme,
            'key_terms': key_terms,
            'description': f'Connecting {len(top_clusters)} major trend clusters',
            'confidence': float(confidence)
        }
    
    def _create_theme_from_terms(self, terms: List[str]) -> str:
        """
        Create a descriptive theme from key terms
        Simple heuristic-based approach
        """
        # Common theme keywords to look for
        tech_keywords = ['ai', 'artificial', 'technology', 'digital', 'computing', 'cyber', 'quantum']
        env_keywords = ['climate', 'environment', 'sustainable', 'renewable', 'carbon', 'ocean']
        social_keywords = ['social', 'mental', 'health', 'inequality', 'privacy', 'work']
        science_keywords = ['space', 'gene', 'medicine', 'quantum', 'research']
        
        # Count occurrences
        categories = {
            'Technology': sum(1 for t in terms for kw in tech_keywords if kw in t.lower()),
            'Environment': sum(1 for t in terms for kw in env_keywords if kw in t.lower()),
            'Society': sum(1 for t in terms for kw in social_keywords if kw in t.lower()),
            'Science': sum(1 for t in terms for kw in science_keywords if kw in t.lower())
        }
        
        # Find top 2 categories
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        top_cats = [cat for cat, count in sorted_cats[:2] if count > 0]
        
        if len(top_cats) >= 2:
            return f"{top_cats[0]} and {top_cats[1]} Trends"
        elif len(top_cats) == 1:
            return f"{top_cats[0]} and Innovation"
        else:
            return "Emerging Global Trends"


if __name__ == "__main__":
    # Test the correlation engine
    demo_trends = [
        {'term': 'artificial intelligence', 'rank': 1},
        {'term': 'machine learning', 'rank': 2},
        {'term': 'climate change', 'rank': 3},
        {'term': 'renewable energy', 'rank': 4},
        {'term': 'quantum computing', 'rank': 5},
        {'term': 'neural networks', 'rank': 6},
        {'term': 'carbon capture', 'rank': 7},
        {'term': 'sustainable farming', 'rank': 8},
    ]
    
    engine = CorrelationEngine()
    result = engine.analyze_trends(demo_trends)
    
    print("\nAnalysis Results:")
    print(f"Unified Topic: {result['unified_topic']['theme']}")
    print(f"Confidence: {result['unified_topic']['confidence']:.2f}")
    print(f"\nClusters: {result['num_clusters']}")
    for cluster in result['clusters']:
        if cluster['label'] != 'noise':
            print(f"  - {cluster['label']}: {', '.join(cluster['terms'][:3])}")
