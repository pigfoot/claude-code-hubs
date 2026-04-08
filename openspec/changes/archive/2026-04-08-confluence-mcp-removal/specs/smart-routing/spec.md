## REMOVED Requirements

### Requirement: Credential Detection — MCP-only scenario
**Reason**: MCP is no longer a routing target. REST API credentials are required for all operations.
**Migration**: Users must set `CONFLUENCE_URL`, `CONFLUENCE_USER`, `CONFLUENCE_API_TOKEN`. The MCP-only path no longer exists.

The following scenario is removed:

> **Scenario: Only MCP is configured**
> - Given `CONFLUENCE_API_TOKEN` environment variable is NOT set
> - When the router checks credentials
> - Then only MCP mode is available
> - And slow operation warnings are enabled

### Requirement: Graceful Fallback
**Reason**: Fallback between MCP and REST API is no longer needed. REST API is the only path.
**Migration**: If REST API fails, the error is surfaced directly. No silent fallback to MCP.

All fallback scenarios (REST→MCP, MCP session expired→REST, MCP expired→re-auth prompt) are removed.

## MODIFIED Requirements

### Requirement: Credential Detection
The system MUST detect available Confluence credentials from environment variables. REST API credentials are required; MCP is not a fallback path.

#### Scenario: API token is configured
- **WHEN** `CONFLUENCE_API_TOKEN`, `CONFLUENCE_URL`, and `CONFLUENCE_USER` are all set
- **THEN** REST API mode is available for all operations

#### Scenario: API token is missing
- **WHEN** any of `CONFLUENCE_API_TOKEN`, `CONFLUENCE_URL`, `CONFLUENCE_USER` is NOT set
- **THEN** the router raises an error with instructions to set the missing variables
- **AND** no MCP fallback is attempted

### Requirement: Operation-Based Routing
The system MUST route all operations to REST API. MCP is not used for any core operation.

#### Scenario: Read operation
- **WHEN** a read operation is requested with REST API credentials available
- **THEN** REST API is used via `read_page.py`

#### Scenario: Write operation
- **WHEN** a write operation is requested with REST API credentials available
- **THEN** REST API is used and operation completes in ~1 second

#### Scenario: CQL search operation
- **WHEN** a CQL search is requested with REST API credentials available
- **THEN** REST API is used via `search_cql.py`

#### Scenario: Rovo search operation
- **WHEN** a Rovo AI search is requested
- **THEN** the built-in Claude Code Atlassian integration (`mcp__claude_ai_Atlassian__searchAtlassian`) is used
- **AND** this is external to the plugin's credential system
