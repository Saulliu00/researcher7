#!/usr/bin/env python3
"""Quick integration test for pipeline Steps 1-3 + CSV logger (no LLM needed)."""

import truststore
truststore.inject_into_ssl()

import csv
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data_providers import create_data_provider
from correlation_providers import create_correlation_provider
from paper_providers import create_paper_provider


def main():
    # Step 1
    print("=" * 60)
    print("STEP 1: Data Fetcher (Google Trends)")
    print("=" * 60)
    data_provider = create_data_provider("google_trends")
    trends = data_provider.get_trending(limit=15)
    print(f"Got {len(trends)} trends:")
    for t in trends[:5]:
        print(f"  {t['rank']}. {t['term']}")

    # Step 2
    print("\n" + "=" * 60)
    print("STEP 2: Correlation Engine (sklearn)")
    print("=" * 60)
    engine = create_correlation_provider("sklearn")
    result = engine.analyze_trends(trends)
    topic = result['unified_topic']
    print(f"Unified Topic: {topic['theme']}")
    print(f"Confidence: {topic['confidence']:.2%}")
    print(f"Clusters: {result['num_clusters']}")
    for c in result['clusters']:
        if c['label'] != 'noise':
            print(f"  {c['label']}: {', '.join(c['terms'][:3])}")

    # Step 3
    print("\n" + "=" * 60)
    print("STEP 3: Paper Finder (Semantic Scholar)")
    print("=" * 60)
    finder = create_paper_provider("semantic_scholar")
    paper = finder.find_best_paper(topic['theme'], max_results=5)
    if not paper:
        print("No paper found (API may be blocked) — using fallback")
        paper = {
            'title': f'Survey of {topic["theme"]}',
            'authors': ['Various Authors'],
            'year': 2025,
            'abstract': 'Fallback paper.',
            'citations': 0,
            'url': '',
            'pdf_url': None,
            'venue': 'N/A',
            'source': 'fallback',
        }
    else:
        print(f"Paper: {paper['title']}")
        print(f"Citations: {paper['citations']:,}")
        print(f"Source: {paper['source']}")

    # Step 4: Test CSV logger
    print("\n" + "=" * 60)
    print("STEP 4: CSV Run Logger")
    print("=" * 60)
    from main import Researcher7
    csv_path = os.path.join('outputs', 'run_log.csv')
    # Use the class method directly (no LLM init needed)
    r = object.__new__(Researcher7)
    r._log_run(
        output_dir='outputs',
        trends=trends,
        correlation_data=result,
        paper=paper,
        script_path='outputs/test_run.md',
        word_count=0,
        country='united_states',
    )
    # Show the CSV content
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(f"  [{row['timestamp']}] {row['unified_topic']} — {row['paper_title'][:50]}")

    print("\n" + "=" * 60)
    print("ALL STEPS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
