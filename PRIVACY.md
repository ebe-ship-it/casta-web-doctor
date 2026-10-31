# Privacy notice

**Status:** Draft notice for an early beta. The maintainer should verify it against the actual hosting provider, logs, analytics, and applicable law before public launch. This notice is not legal advice.

## What this service does

Casta Web Doctor checks a submitted public HTTP(S) website for basic availability, response timing, redirects, HTTPS use, and selected response security headers. It is not a full security audit and does not certify legal or technical compliance.

## Information submitted and processed

When a person requests a scan, the service processes the website address they submit and makes an HTTP request to that destination when scanning is enabled. The hosting platform and infrastructure providers may also process technical connection data, such as IP addresses, request timestamps, and operational logs, under their own terms and retention settings.

The service should not request passwords, authentication tokens, private URLs, or personal data from the site being checked. Do not submit such information in the website-address field.

## Purpose and legal basis

Scan data is processed to perform the requested check, return its result, protect the service against abuse, and troubleshoot reliability or security problems. The maintainer must confirm the applicable legal basis and any registration or notification obligations before operating the public service.

## Retention and sharing

The application is designed not to require an account and sets no-store cache headers for API responses. This alone does **not** prove that hosting, proxy, or platform logs are not retained. Before launch, the maintainer must document actual log sources, access, retention periods, hosting providers, and any international data transfers. Do not promise deletion or zero retention unless verified.

## Security

The scanner is intended to check public destinations only. Public scanning must remain disabled until outbound network protections are implemented and independently verified at the hosting/network layer. Application-level URL validation alone cannot eliminate DNS-rebinding risks.

## Your choices and contact

Do not submit information you are not authorized to share. For questions or requests concerning information processed by this service, contact the service maintainer through the verified contact method published with the live service. A public launch should publish a real contact method and a clear process for privacy requests.

## Updates

This notice may change as the service and its hosting arrangements change. The live version should show the date of its latest review.
