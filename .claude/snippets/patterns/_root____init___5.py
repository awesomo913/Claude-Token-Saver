# From: universal_client.py:83

    def __init__(
        self,
        ai_profile: AIProfile = GEMINI_PROFILE,
        corner: str = "bottom-right",
        use_traffic_control: bool = True,
        traffic_timeout: float = 600.0,
        cdp_port: int = DEFAULT_CDP_PORT,
    ) -> None:
        self._profile = ai_profile
        self._corner = corner
        self._use_traffic = use_traffic_control and TRAFFIC_AVAILABLE
        self._traffic_timeout = traffic_timeout
        self._cdp_port = cdp_port
        self._hwnd: Optional[int] = None
        self._lock = threading.Lock()
        self._cancel_event = threading.Event()
        self._configured = False

        # CDP automation (preferred)
        self._cdp: Optional[CDPChatAutomation] = None
        self._cdp_available = False
