# From: cdp_client.py:60

@dataclass
class CDPSelectors:
    """CSS selectors for interacting with a specific AI chat site.

    Each AI site has different DOM structure. This captures the selectors
    needed to automate that specific site.
    """
    # Input area — where to type the prompt
    input_selector: str = "textarea"
    # Send button (if Enter doesn't work)
    send_button_selector: str = ""
    # Use Enter key to send (most sites)
    send_with_enter: bool = True
    # Response containers — the AI's messages
    response_selector: str = ".message"
    # The last/latest response specifically
    last_response_selector: str = ".message:last-child"
    # Loading/generating indicator (present while AI is typing)
    loading_selector: str = ""
    # Stop button (present while generating, disappears when done)
    stop_button_selector: str = ""
    # Selector for response text content within a response container
    response_text_selector: str = ""
    # Whether input is a contenteditable div (vs textarea)
    input_is_contenteditable: bool = False
    # Additional JS to run after page load (e.g., dismiss popups)
    init_script: str = ""
