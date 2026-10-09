#!/usr/bin/env python3
import re
import shlex
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

SEND_COUNT = 1
CONCURRENT = True
CURL_FILE = "curl.txt"


def with_label_number(data, n):
    if not data:
        return data

    def repl(m):
        base = re.sub(r"\d+$", "", m.group(2))
        return f'{m.group(1)}{base}{n}{m.group(3)}'

    return re.sub(r'("labelName"\s*:\s*")([^"]*)(")', repl, data)


def send_once(n, method, url, headers, cookies, data):
    try:
        requests.request(
            method=method,
            url=url,
            headers=headers,
            cookies=cookies,
            data=data,
            allow_redirects=True,
        )
        return True
    except requests.RequestException:
        return False


def parse_curl(curl_text):
    cleaned = curl_text.replace("\\\n", " ").replace("^\n", " ")
    tokens = shlex.split(cleaned)

    if not tokens or tokens[0] != "curl":
        if tokens and tokens[0] != "curl":
            tokens = ["curl"] + tokens

    method = None
    url = None
    headers = {}
    cookies = {}
    data = None

    i = 1
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
            i += 1
        elif tok.startswith("-"):
            if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
                i += 2
            else:
                i += 1
        else:
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

    mode = "concurrently" if CONCURRENT and SEND_COUNT > 1 else "one by one"
    print(f"Sending {SEND_COUNT} request(s) {mode}...")

    sent = 0
    failed = 0

    if CONCURRENT and SEND_COUNT > 1:
        with ThreadPoolExecutor(max_workers=SEND_COUNT) as pool:
            futures = [
                pool.submit(send_once, n, method, url, headers, cookies,
                            with_label_number(data, n))
                for n in range(1, SEND_COUNT + 1)
            ]
            for future in as_completed(futures):
                if future.result():
                    sent += 1
                else:
                    failed += 1
    else:
        for n in range(1, SEND_COUNT + 1):
            if send_once(n, method, url, headers, cookies, with_label_number(data, n)):
                sent += 1
            else:
                failed += 1

    print(f"Done: {sent}/{SEND_COUNT} request(s) sent" + (f", {failed} failed" if failed else ""))


if __name__ == "__main__":
    main()
