"""Raw signal normalization node."""

from eventflow.schemas import RawSignal


def normalize_signal(raw_signal: RawSignal) -> RawSignal:
    """Return a normalized RawSignal.

    M2 sample data already conforms to the shared RawSignal contract, so this
    node intentionally preserves the validated input object.
    """

    return raw_signal
