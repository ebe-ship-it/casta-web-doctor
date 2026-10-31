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

Casta Web Doctor is a lightweight website-checking tool built with HTML, CSS and JavaScript on the frontend, and Python on the backend. It includes a simple web interface and a command-line scanner.

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

## Run it on your own device

You'll need Python 3.10 or newer and pip.

```bash
git clone https://github.com/ebe-ship-it/casta-web-doctor.git
cd casta-web-doctor
python -m venv .venv
```

Activate the virtual environment with `source .venv/bin/activate` on Linux/macOS/Termux, or `.venv\\Scripts\\Activate.ps1` in Windows PowerShell. Then install dependencies and run locally:

```bash
python -m pip install -r requirements.txt
python webapp.py
```

Open `http://127.0.0.1:5000` in your browser. For production, use a WSGI server:

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

**Safety default:** public scanning is disabled unless `ENABLE_PUBLIC_SCANNING=true` is explicitly configured. Keep it disabled until outbound network isolation, SSRF protections, DNS-rebinding controls, secrets, and production logging have been verified. The `/health` endpoint checks whether the web service is running.

## Run the tests

```bash
python -m pytest -v
```

GitHub Actions runs the test suite when code is pushed to the main branch or a pull request is opened.

## Security and responsible use

Application-level destination checks and redirect validation do not fully prevent DNS-rebinding SSRF. Public scanning requires verified network-level rules that block private networks, link-local addresses, metadata endpoints, and internal services. The current rate limiter uses in-memory storage; limits are process-local and reset on restart. Multi-worker or multi-instance deployments should use shared storage such as Redis.

Only scan websites you own or have permission to assess. Do not use the project to harass a website or overload someone else's service.

## Policies

- [Privacy notice](/privacy)
- [Acceptable use policy](/acceptable-use)
- [Security policy](SECURITY.md)

The privacy notice requires the operator to verify the actual hosting logs, retention settings, and data handling, and to add a real support contact before promoting the service broadly.

## Deploying on Render

The repository includes a `render.yaml` configuration for a Render web service.

1. Open [Render](https://render.com/).
2. Create a new Blueprint and connect this repository.
3. Review the configuration and deploy the service.
4. Test the public website, `/health`, `/privacy`, and `/acceptable-use`.
5. Complete every release-blocking item in [the production security checklist](docs/PRODUCTION_SECURITY_CHECKLIST.md), especially outbound network isolation against SSRF and DNS rebinding.

The initial configuration keeps scanning disabled. Do not enable it until the relevant protections are verified in the actual hosting environment. A deployment configuration does not mean the app is already live.

## Want to help?

- Try it and report bugs.
- Suggest a feature or design improvement.
- Read the code and offer constructive feedback.
- Fork the repository and experiment with your own version.

**Made by Casta 🇹🇿**

GitHub: [@ebe-ship-it](https://github.com/ebe-ship-it)
