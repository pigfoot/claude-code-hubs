# env-standardization Specification

## Purpose

TBD - created by archiving change 005-confluence-smart-routing. Update Purpose after archive.

## Requirements

### Requirement: Environment Variable Naming

The system MUST use standardized environment variable names.

#### Scenario: Read CONFLUENCE_USER for authentication

- **Given** the environment variable `CONFLUENCE_USER` is set to `user@company.com`
- **When** the system reads authentication credentials
- **Then** the user email is read from `CONFLUENCE_USER`
- **And** the value `user@company.com` is used for authentication

#### Scenario: CONFLUENCE_USERNAME is deprecated

- **Given** the environment variable `CONFLUENCE_USERNAME` is set
- **And** `CONFLUENCE_USER` is NOT set
- **When** the system reads authentication credentials
- **Then** `CONFLUENCE_USERNAME` is NOT used
- **And** authentication fails with missing credentials error

### Requirement: Required Environment Variables

The system MUST validate required environment variables for REST API mode.

#### Scenario: All required variables present

- **Given** `CONFLUENCE_URL` is set
- **And** `CONFLUENCE_USER` is set
- **And** `CONFLUENCE_API_TOKEN` is set
- **When** credential validation runs
- **Then** REST API mode is enabled

#### Scenario: Missing CONFLUENCE_URL

- **Given** `CONFLUENCE_URL` is NOT set
- **When** credential validation runs
- **Then** REST API mode is disabled
- **And** MCP fallback mode is used

#### Scenario: Missing CONFLUENCE_USER

- **Given** `CONFLUENCE_USER` is NOT set
- **When** credential validation runs
- **Then** REST API mode is disabled
- **And** MCP fallback mode is used

#### Scenario: Missing CONFLUENCE_API_TOKEN

- **Given** `CONFLUENCE_API_TOKEN` is NOT set
- **When** credential validation runs
- **Then** REST API mode is disabled
- **And** MCP fallback mode is used

### Requirement: Documentation Updates

All documentation MUST reference the standardized variable names.

#### Scenario: README shows correct variable names

- **Given** the `plugins/confluence/README.md` file
- **When** a user reads the Quick Setup section
- **Then** `CONFLUENCE_USER` is shown (not `CONFLUENCE_USERNAME`)

#### Scenario: Code comments use correct names

- **Given** any Python script in the confluence plugin
- **When** environment variables are referenced in comments
- **Then** `CONFLUENCE_USER` is used consistently
