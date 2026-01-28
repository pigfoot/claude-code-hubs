# smart-routing Specification

## Purpose

TBD - created by archiving change 005-confluence-smart-routing. Update Purpose after archive.

## Requirements

### Requirement: Credential Detection

The system MUST detect available Confluence credentials from environment variables.

#### Scenario: API token is configured

- **Given** `CONFLUENCE_API_TOKEN` environment variable is set
- **And** `CONFLUENCE_URL` environment variable is set
- **And** `CONFLUENCE_USER` environment variable is set
- **When** the router checks credentials
- **Then** REST API mode is available
- **And** MCP mode remains available as fallback

#### Scenario: Only MCP is configured

- **Given** `CONFLUENCE_API_TOKEN` environment variable is NOT set
- **When** the router checks credentials
- **Then** only MCP mode is available
- **And** slow operation warnings are enabled

### Requirement: Operation-Based Routing

The system MUST route operations to the optimal API based on operation type.

#### Scenario: Read operation with API token

- **Given** API token credentials are available
- **When** a read operation is requested
- **Then** REST API is used
- **And** operation completes successfully

#### Scenario: Read operation without API token

- **Given** only MCP is available
- **When** a read operation is requested
- **Then** MCP is used
- **And** operation completes successfully

#### Scenario: Write operation with API token

- **Given** API token credentials are available
- **When** a write operation is requested
- **Then** REST API is used
- **And** operation completes in ~1 second

#### Scenario: Write operation without API token

- **Given** only MCP is available
- **When** a write operation is requested
- **Then** a warning is displayed about slow performance
- **And** MCP is used
- **And** operation completes in ~26 seconds

#### Scenario: Rovo search always uses MCP

- **Given** any credential configuration
- **When** a Rovo AI search is requested
- **Then** MCP is used (exclusive feature)
- **And** operation completes successfully

### Requirement: Graceful Fallback

The system MUST fall back to alternative API when the primary fails.

#### Scenario: REST API fails with API token

- **Given** API token credentials are available
- **When** REST API call fails with an error
- **Then** the system falls back to MCP
- **And** logs the fallback event
- **And** completes the operation

#### Scenario: MCP session expires with API token

- **Given** API token credentials are available
- **And** MCP returns "Session not found" error
- **When** the fallback handler is invoked
- **Then** REST API is used silently
- **And** operation completes successfully

#### Scenario: MCP session expires without API token

- **Given** only MCP is available
- **And** MCP returns "Session not found" error
- **When** the fallback handler is invoked
- **Then** user is prompted to re-authenticate via `/mcp`
- **And** operation fails with actionable error message
