# Security policy

## Supported version

Security reports are welcome for the latest code on the default branch. This project is an early beta and is not a full security-audit service.

## Reporting a vulnerability

Please do not publish exploit details, credentials, private URLs, or personal data in public issues. Use GitHub's private vulnerability reporting feature for this repository if it is enabled. If it is unavailable, contact the maintainer privately through a verified contact channel before disclosing details publicly.

Include the affected component, impact, and a minimal reproduction that does not access data you do not own.

## Secrets and credentials

- Never commit API keys, access tokens, passwords, private keys, production environment files, or real credentials.
- Configure deployment secrets in the hosting provider's environment-variable or secret settings. Do not put secrets in HTML, JavaScript delivered to browsers, source control, screenshots, logs, or issue reports.
- Use `.env.example` only for placeholder configuration names and non-sensitive example values.
- If a secret may have been exposed, revoke or rotate it immediately. Removing it from the latest file does not erase it from Git history, forks, logs, or copies.
- Keep local backups and environment files out of Git.

## Scanner safety

Public scanning must remain disabled until outbound network protections are implemented and verified at the hosting/network layer. Application-level URL checks alone cannot eliminate DNS-rebinding races. Do not enable public scanning by setting an environment variable as a substitute for network isolation.
