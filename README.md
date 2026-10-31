Casta Web Doctor 🩺

A lightweight Python tool for checking website availability, response times, HTTPS usage, and common security headers.

Features

- 🌐 Check HTTP response status codes.
- ⚡ Measure response time.
- 🔒 Verify whether the final connection uses HTTPS.
- 🛡️ Identify common security headers that are missing.
- 🔄 Follow HTTP redirects.
- 🧪 Automated tests using pytest.

Requirements

- Python 3.10 or newer
- pip
- Git (optional, for cloning the repository)

Installation

Clone the repository:

git clone https://github.com/ebe-ship-it/casta-web-doctor.git
cd casta-web-doctor

Install the dependencies:

pip install requests pytest

Usage

Check a website:

python main.py https://example.com

You can also provide a domain:

python main.py example.com

The tool reports the HTTP status code, response time, final URL, HTTPS status, and detected security headers.

Run Tests

Run the automated test suite:

python -m pytest -v

Security Notes

Casta Web Doctor provides basic diagnostic information. Missing security headers do not automatically mean a website is vulnerable.

Response times can vary with network conditions, server load, and redirects.

Only test websites you own or have permission to assess.

Project Status

Early development. Features and output may change as the project evolves.

Author

Casta
GitHub: "@ebe-ship-it" (https://github.com/ebe-ship-it)
