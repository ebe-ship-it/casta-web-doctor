# Production security checklist

This checklist distinguishes repository changes from controls that must be verified in the live hosting account. A green CI run is not proof that production is secure.

## Release blockers

- [ ] **Outbound network isolation:** configure infrastructure-level egress controls so the scanner cannot connect to loopback, private, link-local, reserved, multicast, or cloud metadata destinations. Permit only the outbound ports and destinations required for public HTTP/HTTPS scans. Test the rules from the running service. Application DNS checks alone do not eliminate DNS-rebinding or time-of-check/time-of-use races.
- [ ] **DNS rebinding:** verify that the actual network connection cannot reach a prohibited address if a hostname changes DNS answers after validation. Do not mark this complete based only on application destination validation.
- [ ] **Redirects:** verify every redirect hop is revalidated and that egress controls also apply to the connection itself.
- [ ] **Secrets:** inspect deployment environment variables, repository history, logs, and client-side assets. Revoke and rotate any credential that was exposed. Never paste secrets into issues or logs.
- [ ] **Privacy and retention:** confirm the actual hosting provider, access to request logs, fields collected, retention periods, backups, and any third-party processors. Update the privacy notice to reflect verified facts and add a real support contact before promoting the service.
- [ ] **Production configuration:** verify HTTPS, deployment access controls, error handling, CORS, headers, and production health checks on the live host.

## Rate limiting

- The current Render blueprint runs one Gunicorn worker and does not configure Redis. In-memory rate limits are process-local and reset on process restart.
- For a single-process beta, understand and accept that limitation and consider an additional platform-level rate limit.
- For multiple workers or instances, configure a supported shared storage backend such as Redis using the RATELIMIT_STORAGE_URI environment variable, confirm connectivity and authentication, and test that limits are shared across instances.
- TRUST_PROXY_HEADERS=true is only appropriate when the app is behind the expected trusted hosting proxy. Confirm the proxy overwrites forwarded headers and do not expose the WSGI app directly.

## Verification before launch

1. Run python -m pytest -v.
2. Inspect the current deployed version and configuration in the hosting dashboard.
3. Test safe public destinations and confirm private, loopback, link-local, and reserved addresses are rejected.
4. Test redirects to prohibited destinations and confirm no request is made to the destination.
5. Verify network egress restrictions from the deployed service using an approved, controlled test plan.
6. Verify the published privacy and acceptable-use pages are reachable and accurately describe the real deployment.
7. Confirm logs do not contain secrets or unnecessary submitted URL data.
8. Record evidence and date for each completed item.

## Status discipline

Do not mark a control complete because code exists. Mark it complete only after the relevant test or hosting setting has been checked. If the hosting platform cannot provide the required outbound isolation, use a deployment architecture that can, or disable public scanning until the risk is addressed.
