# Security policy

Casta Web Doctor is a small website diagnostic tool and is not a full security audit. Please use it only on websites you own or are authorized to assess.

## Reporting a vulnerability

Please report suspected vulnerabilities privately to the repository owner through GitHub's available private reporting/contact options rather than publishing exploit details in a public issue. Include the affected component, impact, and safe reproduction notes. Do not include real secrets or other people's personal data.

## Deployment warning

The scanner accepts user-supplied destinations, so server-side request forgery (SSRF) is a core risk. Public deployment requires effective outbound network isolation in addition to application-level destination and redirect validation. DNS rebinding and connection-time resolution must be considered. See the production security checklist in docs/PRODUCTION_SECURITY_CHECKLIST.md.

The project does not claim to be production-secure until the hosting configuration, network egress restrictions, secrets, logs, and published policies have been verified.
