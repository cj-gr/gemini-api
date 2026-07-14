import sys
import subprocess
import json
import os
import re
from google import genai
from google.genai import types

def colorize_output(text: str) -> str:
    """Finds risk keywords under the Risk Level header and injects ANSI colors dynamically."""
    RED = "\033[91m\033[1m"      # Critical/High
    YELLOW = "\033[93m\033[1m"   # Medium
    GREEN = "\033[92m\033[1m"    # Low
    RESET = "\033[0m"            # Reset formatting

    color_map = {
        "CRITICAL": RED,
        "HIGH": RED,
        "MEDIUM": YELLOW,
        "LOW": GREEN
    }

    lines = text.split("\n")
    for i, line in enumerate(lines):
        if "Risk Level:" in line and (i + 1) < len(lines):
            next_line = lines[i + 1].upper()

            for keyword, color_code in color_map.items():
                if keyword in next_line:
                    # Relaxed regex: matches the keyword even if surrounded by brackets [] or text
                    lines[i + 1] = re.sub(
                        keyword,
                        f"{color_code}{keyword}{RESET}",
                        lines[i + 1],
                        flags=re.IGNORECASE
                    )
                    break

    return "\n".join(lines)

def handle_pull_request(url: str):
    """Fetches PR data and formats the prompt."""
    try:
        result = subprocess.run(
            ["gh", "pr", "view", url, "--json", "title,body"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)

        system_instruction = """
        You are an expert Senior Software Engineer and Automated Code Reviewer.
        Analyze the provided Pull Request title and description (typically a Dependabot bump).
        Provide a concise evaluation covering exactly these four sections in this order:

        1. **Risk Level:**
        [Classify as strictly LOW, MEDIUM, or HIGH based on the changes, breaking risks, or security patches involved].

        2. **What is changing:**
        (The dependency being upgraded and version jump).

        3. **Risk Assessment:**
        (Provide the reasoning behind the Risk Level. Note any known breaking changes, major version bumps, or security fixes).

        4. **Recommendation:**
        (Should the team Merge immediately, Investigate/Test manually, or Hold?).

        CRITICAL FORMATTING RULE: Whenever you use bold text markdown (**like this**) to highlight a line or a point header, you MUST start the text that follows it on a brand-new line. Never continue prose on the same line as a bold header. Keep your response highly structured, objective, and brief.
        """
        user_prompt = f"TITLE: {data.get('title')}\n\nBODY:\n{data.get('body')}"
        return system_instruction, user_prompt, "Pull Request"
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR: {e.stderr}")
        sys.exit(1)

def handle_security_alert(url: str):
    """Parses alert URL, fetches API metadata, and formats the prompt."""
    pattern = r"github\.com/([^/]+)/([^/]+)/security/dependabot/(\d+)"
    match = re.search(pattern, url)
    if not match:
        print("Error: Invalid Dependabot Alert URL format.")
        sys.exit(1)

    owner, repo, alert_num = match.group(1), match.group(2), match.group(3)

    try:
        api_path = f"repos/{owner}/{repo}/dependabot/alerts/{alert_num}"
        result = subprocess.run(
            ["gh", "api", api_path],
            capture_output=True, text=True, check=True
        )
        alert_data = json.loads(result.stdout)

        system_instruction = """
        You are an expert Cyber Security Engineer and Automated Code Reviewer.
        Analyze the provided GitHub Dependabot Security Alert details.
        Provide a concise triage covering exactly these four sections in this order:

        1. **Risk Level:**
        [Classify as strictly LOW, MEDIUM, HIGH, or CRITICAL based on the advisory severity and actual exploitability vectors].

        2. **Vulnerability Summary:**
        (Briefly explain what the security vulnerability is, how it works, and the library affected).

        3. **Impact & Remediation:**
        (Detail what version range is broken and state exactly what version needs to be targetted for a safe fix).

        4. **Recommendation:**
        (Provide immediate next steps, such as: Upgrade immediately, Mitigate via environment configuration, or Safe to ignore due to development-only dependency scope).

        CRITICAL FORMATTING RULE: Whenever you use bold text markdown (**like this**) to highlight a line or a point header, you MUST start the text that follows it on a brand-new line. Never continue prose on the same line as a bold header. Keep your response highly structured, objective, and brief.
        """

        user_prompt = f"""
        DEPENDENCY: {alert_data.get("dependency", {}).get("package", {}).get("name", "Unknown")}
        GITHUB SEVERITY: {alert_data.get("security_advisory", {}).get("severity", "UNKNOWN").upper()}
        ADVISORY SUMMARY: {alert_data.get("security_advisory", {}).get("summary", "")}
        VULNERABLE RANGE: {alert_data.get("security_vulnerability", {}).get("vulnerable_version_range", "")}
        FIRST PATCHED VERSION: {alert_data.get("security_vulnerability", {}).get("first_patched_version", {}).get("identifier", "None")}
        ADVISORY DETAILS: {alert_data.get("security_advisory", {}).get("description", "")}
        """
        return system_instruction, user_prompt, "Security Alert"
    except subprocess.CalledProcessError as e:
        print(f"Error fetching Security Alert: {e.stderr}")
        sys.exit(1)

def main():
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable not found.")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: dependabot_analyser <GITHUB_URL>")
        sys.exit(1)

    url = sys.argv[1]

    # Route logic based on URL pattern matching
    if "/security/dependabot/" in url:
        system_instruction, user_prompt, target_type = handle_security_alert(url)
    elif "/pull/" in url:
        system_instruction, user_prompt, target_type = handle_pull_request(url)
    else:
        print("Error: URL must be a valid GitHub Pull Request or Dependabot Security Alert link.")
        sys.exit(1)

    print(f"🤖 Context Detected: {target_type}. Querying Gemini...")

    client = genai.Client()
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
        )
    )

    print(f"\n=== Gemini {target_type} Analysis ===")
    print(colorize_output(response.text))
    print("======================================")

if __name__ == "__main__":
    main()
