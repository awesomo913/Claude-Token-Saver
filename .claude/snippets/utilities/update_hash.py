# From: NeoAutocoder/session.py:29
# Update stagnation detection hash.

    def update_hash(self, code: str):
        """Update stagnation detection hash."""
        h = hashlib.md5(code.encode('utf-8')).hexdigest()
        self.hash_history.append(h)
        self.last_hash = h
        if len(self.hash_history) > 5:
            self.hash_history.pop(0)
        return h
