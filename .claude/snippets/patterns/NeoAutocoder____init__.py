# From: NeoAutocoder/core_loop.py:31

    def __init__(self, provider_chain: ProviderChain, output_dir: Path = None):
        self.provider_chain = provider_chain
        self.output_dir = output_dir or (Path.home() / "Downloads" / "neoautocoder")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.recovery = RecoveryManager()
        self.perfection_threshold = 3  # iterations with no improvement → stop
