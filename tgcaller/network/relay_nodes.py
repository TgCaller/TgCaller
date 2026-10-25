"""Registry for relay endpoint configuration.

This stores relay configuration only; it does not establish TURN connections.
"""


class RelayNodes:
    """Maintain a deduplicated list of relay endpoint strings or dictionaries."""

    def __init__(self, nodes=None):
        self._nodes = []
        for node in nodes or ():
            self.add(node)

    def add(self, node):
        """Add an endpoint; return False if it already exists."""
        if not isinstance(node, (str, dict)):
            raise TypeError("relay node must be a string or dictionary")
        if isinstance(node, str) and not node.strip():
            raise ValueError("relay endpoint cannot be empty")
        if isinstance(node, dict) and not node:
            raise ValueError("relay configuration cannot be empty")
        if node in self._nodes:
            return False
        self._nodes.append(dict(node) if isinstance(node, dict) else node)
        return True

    def remove(self, node):
        """Remove an endpoint, returning False when absent."""
        try:
            self._nodes.remove(node)
            return True
        except ValueError:
            return False

    def get_nodes(self):
        """Return a shallow copy of registered relay configurations."""
        return [dict(node) if isinstance(node, dict) else node for node in self._nodes]

    def clear(self):
        self._nodes.clear()

    def __len__(self):
        return len(self._nodes)

    def __iter__(self):
        return iter(self.get_nodes())
