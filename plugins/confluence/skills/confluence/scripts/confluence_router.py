#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""
Confluence Smart Router

Intelligent API selection between MCP and REST API based on:
- Available credentials (environment variables)
- Operation type (read, write, search)
- Performance requirements

Routes to optimal API automatically with graceful fallback.
"""

import os
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class OperationType(Enum):
    """Types of Confluence operations"""

    READ = "read"  # Read page content
    WRITE = "write"  # Update page content
    SEARCH_CQL = "search_cql"  # CQL-based search
    SEARCH_ROVO = "search_rovo"  # Rovo AI semantic search
    UPLOAD = "upload"  # Upload with attachments


class APIMode(Enum):
    """Available API modes"""

    REST_API = "rest_api"  # REST API with token (fast, permanent token)
    MCP = "mcp"  # MCP with OAuth (easy setup, 55-min expiry)


@dataclass
class CredentialConfig:
    """Detected credential configuration"""

    has_rest_api: bool  # REST API credentials available
    has_mcp: bool  # MCP assumed available (OAuth via Claude Code)
    confluence_url: Optional[str] = None
    confluence_user: Optional[str] = None
    # Note: API token is sensitive, not stored in dataclass


@dataclass
class RoutingDecision:
    """Routing decision with rationale"""

    api_mode: APIMode
    reason: str
    warning: Optional[str] = None  # Warning message if applicable
    fallback_available: bool = False


class ConfluenceRouter:
    """Smart router for Confluence API operations"""

    def __init__(self):
        """Initialize router and detect credentials"""
        self.credentials = self._detect_credentials()

    def _detect_credentials(self) -> CredentialConfig:
        """
        Detect available Confluence credentials from environment variables.

        Required for REST API:
        - CONFLUENCE_URL: Base URL (e.g., https://company.atlassian.net/wiki)
        - CONFLUENCE_USER: Email address
        - CONFLUENCE_API_TOKEN: API token

        MCP is assumed available (OAuth handled by Claude Code).

        Returns:
            CredentialConfig with detected credentials
        """
        url = os.getenv("CONFLUENCE_URL")
        user = os.getenv("CONFLUENCE_USER")
        token = os.getenv("CONFLUENCE_API_TOKEN")

        # REST API requires all three variables
        has_rest_api = all([url, user, token])

        # MCP is no longer a routing target. Plugin does not declare MCP.
        has_mcp = False

        return CredentialConfig(
            has_rest_api=has_rest_api,
            has_mcp=has_mcp,
            confluence_url=url,
            confluence_user=user,
        )

    def route_operation(
        self, operation: OperationType, params: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Determine optimal API for the given operation.

        Routing logic:
        - Rovo search → Always MCP (exclusive feature)
        - Read/Search/Upload with REST API token → REST API (faster)
        - Read/Search/Upload without token → MCP (fallback)
        - Write with token → REST API (~1s)
        - Write without token → MCP (~26s) with warning

        Args:
            operation: Type of operation to perform
            params: Optional parameters (reserved for future use)

        Returns:
            RoutingDecision with chosen API mode and rationale
        """
        # Rovo search uses the built-in Claude Code Atlassian integration.
        # This is external to the plugin — use mcp__claude_ai_Atlassian__searchAtlassian.
        if operation == OperationType.SEARCH_ROVO:
            return RoutingDecision(
                api_mode=APIMode.MCP,
                reason=(
                    "Rovo AI search: use built-in mcp__claude_ai_Atlassian__searchAtlassian. "
                    "If not authenticated, call mcp__claude_ai_Atlassian__authenticate first."
                ),
                fallback_available=False,
            )

        # All other operations require REST API credentials
        if not self.credentials.has_rest_api:
            raise ValueError(
                "REST API credentials are required. Please set:\n"
                '  export CONFLUENCE_URL="https://yoursite.atlassian.net/wiki"\n'
                '  export CONFLUENCE_USER="your-email@company.com"\n'
                '  export CONFLUENCE_API_TOKEN="your-token"\n'
                "\nGenerate token: https://id.atlassian.com/manage-profile/security/api-tokens"
            )

        if operation in [
            OperationType.READ,
            OperationType.SEARCH_CQL,
            OperationType.UPLOAD,
        ]:
            return RoutingDecision(
                api_mode=APIMode.REST_API,
                reason="REST API for read/search operations",
                fallback_available=False,
            )

        # WRITE
        return RoutingDecision(
            api_mode=APIMode.REST_API,
            reason="REST API provides fast writes (~1 second)",
            fallback_available=False,
        )

    def handle_fallback(
        self,
        original_operation: OperationType,
        original_mode: APIMode,
        error: Exception,
    ) -> Optional[RoutingDecision]:
        """
        Handle REST API failure. No MCP fallback — REST API is the only path.

        Args:
            original_operation: The operation that failed
            original_mode: The API mode that failed
            error: The error that occurred

        Returns:
            None (no fallback available)
        """
        print(
            f"❌ REST API error for {original_operation.value}: {error}\n"
            "   Check your credentials and network connectivity.",
            file=sys.stderr,
        )
        return None

    def get_status(self) -> Dict[str, Any]:
        """
        Get current router status and configuration.

        Returns:
            Dict with status information
        """
        return {
            "rest_api_available": self.credentials.has_rest_api,
            "mcp_available": False,
            "primary_mode": (
                "REST API" if self.credentials.has_rest_api else "Not configured"
            ),
            "credentials": {
                "confluence_url": self.credentials.confluence_url or "Not set",
                "confluence_user": self.credentials.confluence_user or "Not set",
                "confluence_api_token": "Set"
                if os.getenv("CONFLUENCE_API_TOKEN")
                else "Not set",
            },
        }

    def log_decision(self, operation: OperationType, decision: RoutingDecision):
        """
        Log routing decision for transparency.

        Args:
            operation: The operation being routed
            decision: The routing decision
        """
        print(
            f"🔀 Router: {operation.value} → {decision.api_mode.value}", file=sys.stderr
        )
        print(f"   Reason: {decision.reason}", file=sys.stderr)
        if decision.warning:
            print(f"   {decision.warning}", file=sys.stderr)


def main():
    """CLI interface for testing the router"""
    print("Confluence Smart Router - Status Check")
    print("=" * 50)

    router = ConfluenceRouter()
    status = router.get_status()

    print("\nConfiguration:")
    print(
        f"  REST API Available: {'✅ Yes' if status['rest_api_available'] else '❌ No'}"
    )
    print(f"  MCP Available: {'✅ Yes' if status['mcp_available'] else '❌ No'}")
    print(f"  Primary Mode: {status['primary_mode']}")

    print("\nCredentials:")
    for key, value in status["credentials"].items():
        print(f"  {key}: {value}")

    print("\nRouting Examples:")
    operations = [
        OperationType.READ,
        OperationType.WRITE,
        OperationType.SEARCH_CQL,
        OperationType.SEARCH_ROVO,
        OperationType.UPLOAD,
    ]

    for op in operations:
        decision = router.route_operation(op)
        print(f"\n  {op.value}:")
        print(f"    → {decision.api_mode.value}")
        print(f"    Reason: {decision.reason}")
        if decision.warning:
            print(f"    ⚠️  {decision.warning[:60]}...")


if __name__ == "__main__":
    main()
