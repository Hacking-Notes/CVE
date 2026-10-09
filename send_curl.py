#!/usr/bin/env python3
"""Read a curl command (copied as 'bash' for curl) from curl.txt and replay it with requests.

Set SEND_COUNT below to how many times you want to send it (e.g. 1 or 2).
"""

import shlex
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# ---------------------------------------------------------------------------
# How many times to send the request. Change this to 1 or 2 (or any number).
SEND_COUNT = 1
# Send the requests concurrently (in parallel) instead of one after another.
# When SEND_COUNT is 2 or 3, they fire almost at the same time so you don't wait.
CONCURRENT = True
# File that holds the curl command copied as bash.
CURL_FILE = "curl.txt"
# ---------------------------------------------------------------------------


def send_once(n, method, url, headers, cookies, data):
    """Send the request once and return (n, result_string)."""
    try:
        resp = requests.request(
            method=method,
            url=url,
            headers=headers,
            cookies=cookies,
            data=data,
            allow_redirects=True,
        )
        line = f"[{n}/{SEND_COUNT}] {resp.status_code} {resp.reason} ({len(resp.content)} bytes)"
        return n, line, resp
    except requests.RequestException as exc:
        return n, f"[{n}/{SEND_COUNT}] ERROR: {exc}", None


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
    mode = "concurrently" if CONCURRENT and SEND_COUNT > 1 else "one by one"
    print(f"Sending {SEND_COUNT} time(s) {mode}...\n")

    last_resp = None

    if CONCURRENT and SEND_COUNT > 1:
        # Fire all requests at once and print results as they come back.
        with ThreadPoolExecutor(max_workers=SEND_COUNT) as pool:
            futures = [
                pool.submit(send_once, n, method, url, headers, cookies, data)
                for n in range(1, SEND_COUNT + 1)
            ]
            for future in as_completed(futures):
                _, line, resp = future.result()
                print(line)
                if resp is not None:
                    last_resp = resp
    else:
        # Send sequentially.
        for n in range(1, SEND_COUNT + 1):
            _, line, resp = send_once(n, method, url, headers, cookies, data)
            print(line)
            if resp is not None:
                last_resp = resp

    if last_resp is not None:
        print("\nLast response body (first 500 chars):")
        print(last_resp.text[:500])


if __name__ == "__main__":
    main()
