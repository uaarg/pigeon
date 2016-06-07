class Exporter:
    """
    Base class for all exporters. They should inherit this class
    and implement it's signature.
    """
    def export(self, features, path):
        raise(NotImplementedError())