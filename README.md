# Dependabot Analyser

An automated command-line tool powered by the Gemini API (`gemini-2.5-flash`) that reviews GitHub Pull Requests and Dependabot Security Alerts directly from your terminal. It uses the official GitHub CLI to securely parse context and outputs colour-coded risk metrics, impact evaluations, and manual testing recommendations.

---

## Prerequisites
Before setting up the Python environment, you must install and authenticate the official GitHub CLI tool (`gh`). This handles access permissions for your public or private enterprise repositories.

* **Install via Homebrew (macOS):**
  ```bash
  brew install gh
Authenticate your account:

Bash
gh auth login

## Python Dependencies
Install the modern, official Google GenAI SDK using pip. This library handles all communication with the Gemini API models.

Bash
pip install google-genai
Environment Variables
The script relies on your global terminal instance to store both your secure API token and the short-hand command alias. Add these lines to your terminal configuration profile (~/.zshrc or ~/.bashrc):

Bash
# Open your configuration profile
nano ~/.zshrc

# Append these two lines at the bottom (replace placeholder with your actual key)
export GEMINI_API_KEY="AIzaSyYourActualKeyHere..."
alias dependabot_analyser='python3 ~/Downloads/gemini-api/dependabot_analyser.py'
Note: Run source ~/.zshrc in your terminal to reload and activate these changes immediately.

How the Script Works
The tool operates as a single, multi-routed contextual scanner that processes URLs sequentially:

URL Interception: When you pass a link argument, regex patterns identify whether the target string is a Pull Request (/pull/) or a Security Advisory Alert (/security/dependabot/).

Metadata Gathering: * For PRs, it triggers gh pr view to fetch raw markdown bodies and titles.

For Security Alerts, it communicates directly with GitHub's REST API (gh api repos/...) to retrieve underlying CVE impact indices and vendor advisory logs.

Structured System Prompting: It hands data over to Gemini using explicit engineering personas, ensuring responses use consistent formatting with line-breaks after bold markdown headers.

Output Post-Processing: A terminal filter parses the dynamic response text, mapping security keywords (LOW, MEDIUM, HIGH, CRITICAL) to vibrant ANSI terminal font colours for immediate scannability.

Usage
Once your environment variables and terminal alias are configured, execute the command from any terminal directory by passing the target GitHub link.

Analyzing a Pull Request
Bash
dependabot_analyser [https://github.com/owner/repo/pull/123](https://github.com/owner/repo/pull/123)
Analyzing a Dependabot Security Alert
Bash
dependabot_analyser [https://github.com/owner/repo/security/dependabot/575](https://github.com/owner/repo/security/dependabot/575)
Expected Output Example
Plaintext
🤖 Context Detected: Security Alert. Querying Gemini...

=== Gemini Security Alert Analysis ===
**Risk Level:**
HIGH

**Vulnerability Summary:**
Regular Expression Denial of Service (ReDoS) vulnerability detected in the `template` function...

**Impact & Remediation:**
Vulnerable versions span >= 4.17.0, < 4.17.21. Upgrade immediately to version 4.17.21.

**Recommendation:**
Upgrade version parameters immediately. High Risk: do not auto-merge without local verification.
======================================
