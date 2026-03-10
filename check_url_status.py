import sys
import io

# Force UTF-8 output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import urllib.request
import urllib.error



# HTTP status code descriptions
STATUS_DESCRIPTIONS = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found (Temporary Redirect)",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}


def check_url_status(url: str) -> None:
    """Check the HTTP status code of a given URL and print the result."""

    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
        print(f"  (No scheme provided — assuming: {url})")

    print(f"\n[>>] Checking: {url}")
    print("-" * 50)

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (URL Status Checker)"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.status
            description = STATUS_DESCRIPTIONS.get(status_code, "Unknown")
            print(f"  [OK] Status Code : {status_code}")
            print(f"  [--] Description : {description}")
            print(f"  [>>] Final URL   : {response.url}")

    except urllib.error.HTTPError as e:
        status_code = e.code
        description = STATUS_DESCRIPTIONS.get(status_code, "Unknown")
        print(f"  [ERR] Status Code : {status_code}")
        print(f"  [--] Description : {description}")

    except urllib.error.URLError as e:
        print(f"  [!] Connection Error: {e.reason}")

    except TimeoutError:
        print("  [!] Request timed out (10s limit).")

    except Exception as e:
        print(f"  [ERR] Unexpected error: {e}")

    print("-" * 50)


def main():
    # Check if a URL was passed as a command-line argument
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("\nEnter URL to check: ").strip()

    if not url:
        print("[ERR] No URL provided. Exiting.")
        sys.exit(1)

    check_url_status(url)


if __name__ == "__main__":
    main()
