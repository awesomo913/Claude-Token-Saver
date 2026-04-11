"""CDP diagnostic and testing utility.

Run this to verify CDP is working with your browser:
    python -m gemini_coder_web.cdp_test

It will:
1. Check if Chrome is running with debugging enabled
2. List all available tabs
3. Try to connect to each AI chat tab it finds
4. Test basic DOM operations (find input, count messages, etc.)
"""

import sys
import time
from .cdp_client import (
    discover_cdp_targets,
    is_cdp_available,
    CDPConnection,
    CDPChatAutomation,
    get_selectors_for_profile,
    launch_chrome_with_cdp,
    DEFAULT_CDP_PORT,
    SELECTOR_PRESETS,
)


def _detect_ai_site(url: str) -> str:
    """Detect which AI site a URL belongs to."""
    url_lower = url.lower()
    if "gemini.google.com" in url_lower:
        return "Gemini"
    if "chatgpt.com" in url_lower or "chat.openai.com" in url_lower:
        return "ChatGPT"
    if "claude.ai" in url_lower:
        return "Claude"
    if "openrouter.ai" in url_lower:
        return "OpenRouter"
    if "copilot.microsoft.com" in url_lower:
        return "Copilot"
    return ""


def run_diagnostics(port: int = DEFAULT_CDP_PORT) -> None:
    """Run full CDP diagnostics."""
    print("=" * 60)
    print("  Autocoder CDP Diagnostics")
    print("=" * 60)
    print()

    # Step 1: Check CDP availability
    print("[1] Checking CDP availability on port %d..." % port)
    if not is_cdp_available(port):
        print("  FAIL: No CDP connection.")
        print()
        print("  Chrome must be running with --remote-debugging-port=%d" % port)
        print("  Close ALL Chrome windows, then run:")
        print()
        print("    chrome.exe --remote-debugging-port=%d" % port)
        print()
        print("  Or click 'Launch CDP Browser' in Autocoder's Settings.")
        print()

        answer = input("  Launch Chrome with CDP now? [y/N] ").strip().lower()
        if answer == "y":
            print("  Launching Chrome with CDP...")
            ok = launch_chrome_with_cdp(port=port)
            if ok:
                print("  OK! Chrome launched with CDP.")
            else:
                print("  FAIL: Could not launch Chrome.")
                return
        else:
            return
    else:
        print("  OK: CDP is available!")

    print()

    # Step 2: List all tabs
    print("[2] Discovering browser tabs...")
    targets = discover_cdp_targets(port)
    print(f"  Found {len(targets)} tab(s):")
    for i, t in enumerate(targets):
        ai = _detect_ai_site(t.url)
        tag = f" [{ai}]" if ai else ""
        print(f"  [{i+1}] {t.title[:50]}{tag}")
        print(f"      URL: {t.url[:70]}")
    print()

    # Step 3: Test each AI tab
    ai_tabs = [(t, _detect_ai_site(t.url)) for t in targets if _detect_ai_site(t.url)]
    if not ai_tabs:
        print("[3] No AI chat tabs found!")
        print("  Open an AI chat (Gemini, ChatGPT, Claude, OpenRouter)")
        print("  in the CDP browser, then run this test again.")
        return

    print(f"[3] Testing {len(ai_tabs)} AI chat tab(s)...")
    print()

    for target, ai_name in ai_tabs:
        print(f"  --- {ai_name} ({target.title[:40]}) ---")

        # Connect
        conn = CDPConnection(target.ws_url)
        if not conn.connect():
            print("    FAIL: Could not connect via WebSocket")
            continue
        print("    OK: WebSocket connected")

        selectors = get_selectors_for_profile(ai_name)
        chat = CDPChatAutomation(conn, selectors, ai_name)

        # Test: page URL
        url = conn.get_page_url()
        print(f"    URL: {url[:60]}")

        # Test: find input
        input_found = False
        for sel in selectors.input_selector.split(","):
            sel = sel.strip()
            if conn.find_element(sel):
                print(f"    OK: Input found ({sel[:40]})")
                input_found = True
                break
        if not input_found:
            print(f"    WARN: Input not found with any selector")
            print(f"         Tried: {selectors.input_selector[:70]}")

        # Test: find send button
        if selectors.send_button_selector:
            btn_found = False
            for sel in selectors.send_button_selector.split(","):
                sel = sel.strip()
                if conn.find_element(sel):
                    print(f"    OK: Send button found ({sel[:40]})")
                    btn_found = True
                    break
            if not btn_found:
                if selectors.send_with_enter:
                    print(f"    INFO: Send button not found (uses Enter key)")
                else:
                    print(f"    WARN: Send button not found")

        # Test: count existing responses
        response_count = 0
        for sel in selectors.response_selector.split(","):
            sel = sel.strip()
            count = conn.count_elements(sel)
            if count > 0:
                response_count = count
                break
        print(f"    Responses on page: {response_count}")

        # Test: read last response
        if response_count > 0:
            text = chat.read_last_response()
            if text:
                preview = text[:80].replace("\n", " ")
                print(f"    Last response: \"{preview}...\"")
            else:
                print(f"    WARN: Could not read last response text")

        # Test: check for loading indicator
        if selectors.loading_selector:
            loading = False
            for sel in selectors.loading_selector.split(","):
                sel = sel.strip()
                if conn.find_element(sel):
                    loading = True
                    break
            print(f"    Currently generating: {'Yes' if loading else 'No'}")

        conn.disconnect()
        print()

    print("=" * 60)
    print("  Diagnostics complete!")
    print("=" * 60)


if __name__ == "__main__":
    port = DEFAULT_CDP_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_diagnostics(port)
