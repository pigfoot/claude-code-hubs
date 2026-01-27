#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""
Confluence Smart Search

Detect search result precision and suggest alternatives when results may be low quality.

Features:
- Calculate confidence score based on title matches and result count
- Suggest CQL alternative when Rovo results are imprecise
- Generate CQL preview query for user

Usage:
    from smart_search import SmartSearch

    search = SmartSearch()
    results = [...search results from Rovo...]
    analysis = search.analyze_results("WRS documentation", results)

    if analysis.should_suggest_cql:
        print(analysis.suggestion)
        print(f"Try CQL: {analysis.cql_query}")
"""

import re
import sys
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class SearchAnalysis:
    """Search result quality analysis"""
    query: str
    total_results: int
    title_matches: int
    confidence: float
    confidence_level: str  # "high", "medium", "low", "zero"
    should_suggest_cql: bool
    suggestion: Optional[str] = None
    cql_query: Optional[str] = None


class SmartSearch:
    """Smart search quality detection and CQL suggestion"""

    # Confidence thresholds
    HIGH_CONFIDENCE = 0.9
    MEDIUM_CONFIDENCE = 0.7
    LOW_CONFIDENCE = 0.4
    SUGGESTION_THRESHOLD = 0.6

    def __init__(self):
        """Initialize smart search analyzer"""
        pass

    def calculate_confidence(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence score for search results.

        Scoring factors:
        - Title match count (primary indicator)
        - Keyword overlap rate
        - Result count (too many = low precision)

        Confidence levels:
        - >= 0.9: High (3+ title matches)
        - 0.7-0.9: Medium (1-2 title matches)
        - <= 0.4: Low (many results, few title matches)
        - 0.0: Zero (no results)

        Args:
            query: Original search query
            results: List of search results (each with 'title' field)

        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not results:
            return 0.0

        total_results = len(results)

        # Count title matches (case-insensitive, partial match)
        query_lower = query.lower()
        title_matches = sum(
            1 for result in results
            if query_lower in result.get("title", "").lower()
        )

        # Calculate confidence based on title matches
        if title_matches >= 3:
            base_confidence = 0.9
        elif title_matches == 2:
            base_confidence = 0.8
        elif title_matches == 1:
            base_confidence = 0.7
        else:
            base_confidence = 0.3

        # Adjust down if too many results (low precision indicator)
        if total_results > 50:
            # Many results with few matches = low precision
            base_confidence *= 0.5

        # Adjust up if few results and good matches
        if total_results <= 10 and title_matches > 0:
            # Focused results = high confidence
            match_ratio = title_matches / total_results
            base_confidence = min(1.0, base_confidence * (1 + match_ratio * 0.2))

        return round(base_confidence, 2)

    def generate_cql_query(self, query: str) -> str:
        """
        Generate CQL query preview for the user.

        Format: title ~ "query" OR text ~ "query"

        Args:
            query: Original search query

        Returns:
            CQL query string
        """
        # Escape special CQL characters
        escaped_query = self._escape_cql(query)

        # Generate title + text search CQL
        cql = f'title ~ "{escaped_query}" OR text ~ "{escaped_query}"'

        return cql

    def _escape_cql(self, query: str) -> str:
        r"""
        Escape special characters in CQL query.

        Special characters in CQL: " \ (need escaping)

        Args:
            query: Raw query string

        Returns:
            Escaped query string
        """
        # Escape backslashes first (must be done first)
        escaped = query.replace("\\", "\\\\")

        # Escape double quotes
        escaped = escaped.replace('"', '\\"')

        return escaped

    def analyze_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> SearchAnalysis:
        """
        Analyze search results and generate suggestions.

        Args:
            query: Original search query
            results: Search results from Rovo

        Returns:
            SearchAnalysis with confidence score and suggestions
        """
        total_results = len(results)

        # Count title matches
        query_lower = query.lower()
        title_matches = sum(
            1 for result in results
            if query_lower in result.get("title", "").lower()
        )

        # Calculate confidence
        confidence = self.calculate_confidence(query, results)

        # Determine confidence level
        if confidence >= self.HIGH_CONFIDENCE:
            level = "high"
        elif confidence >= self.MEDIUM_CONFIDENCE:
            level = "medium"
        elif confidence > 0:
            level = "low"
        else:
            level = "zero"

        # Should suggest CQL?
        should_suggest = confidence < self.SUGGESTION_THRESHOLD

        # Generate suggestion if needed
        suggestion = None
        cql_query = None
        if should_suggest and total_results > 0:
            cql_query = self.generate_cql_query(query)
            suggestion = self._generate_suggestion(
                query, total_results, title_matches, confidence, cql_query
            )

        return SearchAnalysis(
            query=query,
            total_results=total_results,
            title_matches=title_matches,
            confidence=confidence,
            confidence_level=level,
            should_suggest_cql=should_suggest,
            suggestion=suggestion,
            cql_query=cql_query
        )

    def _generate_suggestion(
        self,
        query: str,
        total_results: int,
        title_matches: int,
        confidence: float,
        cql_query: str
    ) -> str:
        """
        Generate user-facing suggestion message (bilingual: EN + ZH-TW).

        Args:
            query: Original query
            total_results: Total number of results
            title_matches: Number of title matches
            confidence: Confidence score
            cql_query: Generated CQL query

        Returns:
            Formatted suggestion message
        """
        suggestion = (
            f"ℹ️  Search precision may be low (confidence: {confidence:.0%}).\n"
            f"   Found {total_results} results, but only {title_matches} title match(es) for '{query}'.\n"
            f"\n"
            f"   Consider using CQL search for more precise results:\n"
            f"   CQL 查詢可能提供更精確的結果：\n"
            f"   {cql_query}\n"
        )
        return suggestion


def main():
    """CLI interface for testing smart search"""
    if len(sys.argv) < 2:
        print("Usage: python smart_search.py <query>")
        print()
        print("Example:")
        print("  python smart_search.py 'WRS documentation'")
        sys.exit(1)

    query = sys.argv[1]

    # Mock results for testing
    mock_results = [
        {"title": "Introduction to WRS", "id": "1"},
        {"title": "WRS API Reference", "id": "2"},
        {"title": "Getting Started", "id": "3"},
        {"title": "Configuration Guide", "id": "4"},
    ]

    search = SmartSearch()
    analysis = search.analyze_results(query, mock_results)

    print(f"Search Analysis for: '{query}'")
    print("=" * 50)
    print(f"Total Results: {analysis.total_results}")
    print(f"Title Matches: {analysis.title_matches}")
    print(f"Confidence: {analysis.confidence:.0%} ({analysis.confidence_level})")
    print(f"Should Suggest CQL: {analysis.should_suggest_cql}")

    if analysis.should_suggest_cql:
        print()
        print(analysis.suggestion)
        print(f"CQL Query: {analysis.cql_query}")


if __name__ == "__main__":
    main()
