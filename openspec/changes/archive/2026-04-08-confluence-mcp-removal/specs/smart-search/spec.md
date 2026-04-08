## REMOVED Requirements

### Requirement: CQL Preview Generation
**Reason**: CQL is now the primary search path. When CQL results are low-quality, the system suggests Rovo AI search (not CQL). Generating a CQL preview is no longer meaningful.
**Migration**: The `generate_cql_query()` method can be removed or kept as a private utility; it is no longer surfaced in suggestions.

## MODIFIED Requirements

### Requirement: Precision Warning
The system MUST suggest Rovo AI search when CQL search results are imprecise, and users should be offered the opportunity to authenticate and retry with semantic search.

#### Scenario: Suggest Rovo for low confidence CQL results
- **WHEN** CQL search results have confidence < 0.6
- **THEN** a suggestion is included in the output
- **AND** the suggestion asks whether the user wants to try Rovo AI search
- **AND** the suggestion notes that Rovo requires Atlassian authentication

#### Scenario: No suggestion for high confidence CQL results
- **WHEN** CQL search results have confidence >= 0.6
- **THEN** no suggestion is included
- **AND** results are returned directly
