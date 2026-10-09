#!/usr/bin/env python3
"""Read a curl command (copied as 'bash' for curl) from curl.txt and replay it with requests.

Set SEND_COUNT below to how many times you want to send it (e.g. 1 or 2).
"""

import shlex
import sys

import requests

# ---------------------------------------------------------------------------
# How many times to send the request. Change this to 1 or 2 (or any number).
SEND_COUNT = 1
# File that holds the curl command copied as bash.
CURL_FILE = "curl.txt"
# ---------------------------------------------------------------------------


def parse_curl(curl_text):
    """Turn a 'copy as bash' curl command into pieces requests can use."""
    # Join line continuations ("\" at end of line) into one logical line.
    cleaned = curl_text.replace("\\\n", " ").replace("^\n", " ")
    tokens = shlex.split(cleaned)

    if not tokens or tokens[0] != "curl":
        # Some copies drop the leading "curl"; tolerate that.
        if tokens and tokens[0] != "curl":
            tokens = ["curl"] + tokens

    method = None
    url = None
    headers = {}
    cookies = {}
    data = None

    i = 1  # skip "curl"
    while i < len(tokens):
        tok = tokens[i]

        if tok in ("-X", "--request"):
            method = tokens[i + 1]
            i += 2
        elif tok in ("-H", "--header"):
            header = tokens[i + 1]
            if ":" in header:
                name, _, value = header.partition(":")
                headers[name.strip()] = value.strip()
            i += 2
        elif tok in ("-b", "--cookie"):
            cookie_str = tokens[i + 1]
            for part in cookie_str.split(";"):
                if "=" in part:
                    k, _, v = part.partition("=")
                    cookies[k.strip()] = v.strip()
            i += 2
        elif tok in ("-d", "--data", "--data-raw", "--data-binary",
                     "--data-ascii", "--data-urlencode"):
            data = tokens[i + 1] if data is None else data + "&" + tokens[i + 1]
            i += 2
        elif tok in ("--url",):
            url = tokens[i + 1]
            i += 2
        elif tok in ("--compressed", "-L", "--location", "-k", "--insecure",
                     "-s", "--silent", "-i", "--include", "-v", "--verbose",
                     "-S", "--show-error", "-g", "--globoff"):
            # Flags with no argument that don't change the request itself.
            i += 1
        elif tok.startswith("-"):
            # Unknown option; skip it and its value if it looks like it takes one.
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                i += 2
            else:
                i += 1
        else:
            # Bare token = the URL.
            if url is None:
                url = tok
            i += 1

    if method is None:
        method = "POST" if data is not None else "GET"

    if url is None:
        raise ValueError("No URL found in curl.txt")

    return method.upper(), url, headers, cookies, data


def main():
    try:
        with open(CURL_FILE, "r", encoding="utf-8") as fh:
            curl_text = fh.read().strip()
    except FileNotFoundError:
        sys.exit(f"Could not find '{CURL_FILE}'. Paste your curl command into it first.")

    if not curl_text:
        sys.exit(f"'{CURL_FILE}' is empty. Paste your curl command (copied as bash) into it.")

    method, url, headers, cookies, data = parse_curl(curl_text)

    print(f"Parsed: {method} {url}")
    print(f"Headers: {len(headers)} | Cookies: {len(cookies)} | Body: {'yes' if data else 'no'}")
    print(f"Sending {SEND_COUNT} time(s)...\n")

    for n in range(1, SEND_COUNT + 1):
        resp = requests.request(
            method=method,
            url=url,
            headers=headers,
            cookies=cookies,
            data=data,
            allow_redirects=True,
        )
        print(f"[{n}/{SEND_COUNT}] {resp.status_code} {resp.reason} "
              f"({len(resp.content)} bytes)")

    print("\nLast response body (first 500 chars):")
    print(resp.text[:500])


if __name__ == "__main__":
    main()
