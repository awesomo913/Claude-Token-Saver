# From: NeoAutocoder/provider_chain.py:29

    def __init__(self, config_dir: Path = None):
        if config_dir is None:
            config_dir = Path.home() / ".neoautocoder"
        self.config_dir = config_dir
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.providers: List[ProviderEntry] = []
        self.current_index = 0
        self.rotation_interval = 5  # iterations before forced rotation
        self.iter_since_rotation = 0
        
        self._register_providers()
