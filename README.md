# Casta Web Doctor 🩺🌐

### I'm young, I'm learning, and I want to build things that make a difference.

Hey! I'm Casta, a young developer from Tanzania who's been teaching myself how to make websites. I'm still learning, still experimenting, and definitely still figuring things out, but I believe you don't have to be an expert or have a big team before you start building something useful.

As I've been making my own websites, I kept wanting a simple way to test them and understand how they were doing. Was a website responding? Was it using HTTPS? How long did it take to respond? Were some common security headers missing?

So I started building **Casta Web Doctor**: a small tool I could use to check websites and learn more about what happens behind the scenes.

At first, this was mainly for testing my own projects. Then I thought: why keep it to myself? Other people are learning to build websites too, and maybe this project could help someone else test their work, learn something new, or get an idea for their own project.

**That's why I'm sharing this repository publicly.** It's not a giant company product or a perfect, finished tool. It's a project made by a young person who wants to learn, improve, and contribute something useful. I'm sharing the code so people can try it, learn from it, give feedback, and hopefully help make it better.

If you're learning web development too, you're welcome here. You don't need to know everything before you start. 🌱

---

## What is Casta Web Doctor?

Casta Web Doctor is a lightweight website-checking tool built with regular HTML, CSS and JavaScript on the frontend, and Python on the backend. It includes a simple web interface and a command-line scanner.

It checks a few practical things about a public website:

- **HTTP status:** did the website respond, and what status did it return?
- **Response time:** how long it took to receive response headers, including redirects.
- **HTTPS:** does the final connection use HTTPS?
- **Redirects:** how many redirects happened, and where did the request end up?
- **Security headers:** are five common browser security headers present?
- **Plain-language explanations:** what do those headers generally do?

The goal is to make these basic checks easier to understand, especially if you're still learning.

## A little note

This project is a work in progress. I expect to find bugs, improve the design, and add useful features as I learn. If you notice something broken or have an idea that could make it better, please open an issue or share constructive feedback.

Please remember that this is a **basic diagnostic tool, not a full security audit**. A missing header does not automatically mean a website is vulnerable, and a successful scan does not prove a website is safe.

## Built with

- HTML, CSS and JavaScript
- Python and Flask
- Requests
- Flask-Limiter
- Pytest and GitHub Actions

The frontend uses normal web files rather than a site builder or a large frontend framework. I wanted to understand and work with the code directly.

## Run it on your own device

You'll need Python 3.10 or newer and pip.

### 1. Get the code

```bash
git clone https://github.com/ebe-ship-it/casta-web-doctor.git
cd casta-web-doctor
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

- **Linux/macOS/Termux:** `source .venv/bin/activate`
- **Windows PowerShell:** `.venv\\Scripts\\Activate.ps1`

### 3. Install the dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the app

```bash
python webapp.py
```

Then open **http://127.0.0.1:5000** in your browser.

For production, use a WSGI server rather than Flask's development server:

```bash
gunicorn webapp:app --workers 1 --threads 8 --timeout 30
```

## API example

The app accepts a JSON POST request at `/api/scan`:

```json
{
  "url": "https://example.com"
}
```

The response contains the scan results in JSON. For live scanner milestones, send the same JSON payload to `POST /api/scan/stream`; it returns Server-Sent Events containing actual scanner progress events and a final result event. The `/health` endpoint can be used to check whether the app is running.

## Run the tests

```bash
python -m pytest -v
```

GitHub Actions runs the test suite when code is pushed to the main branch or a pull request is opened.

## Security and responsible use

The scanner accepts HTTP and HTTPS on their standard ports, checks destinations before requesting them, and validates redirects. It also includes request limits and basic security headers for the app itself.

There are still limitations. DNS can change between validation and a request, so application-level checks alone cannot fully prevent DNS-rebinding SSRF. A public deployment needs network-level rules that block access to private networks and internal services. To avoid pretending application-level DNS checks are sufficient, the scanner currently fails closed on Render unconditionally. An environment variable is not a firewall, and the standard Render Blueprint does not configure a network egress firewall. Do not enable public scanning until the hosting environment has real outbound controls that block private, loopback, link-local, and internal destinations, and those controls have been tested. The current rate limiter uses in-memory storage, which is intended for a small beta; a larger multi-instance deployment should use shared storage such as Redis.

Only scan websites you own or have permission to assess. Please don't use this project to harass a website or overload someone else's service.

## Deploying on Render

The repository includes a `render.yaml` configuration for a Render web service.

1. Open [Render](https://render.com/).
2. Create a new Blueprint and connect this repository.
3. Review the configuration and start the deployment.
4. Before enabling scans on a public deployment, configure and verify outbound network controls that block private, loopback, link-local, and internal service destinations. Until then, Render-hosted scans intentionally return a security configuration error. Live progress streaming does not bypass this guard; it reports that the scan was blocked. The `/health` endpoint can still confirm the service is running.

A deployment configuration doesn't mean the app is already live. Hosting plans and platform settings can change, so review the current options in your Render account.

## Want to help?

If you're interested in the project:

- Try it and report bugs.
- Suggest a feature or a design improvement.
- Read the code and tell me what I could do better.
- Fork the repository and experiment with your own version.

I'm learning as I go, so respectful feedback is genuinely welcome. If this project helps you, or inspires you to build something of your own, then that's already a win.

Thanks for checking out something I made. This is one step in a much longer journey, and I'm excited to keep learning and building.

**Made by Casta 🇹🇿**

GitHub: [@ebe-ship-it](https://github.com/ebe-ship-it)
