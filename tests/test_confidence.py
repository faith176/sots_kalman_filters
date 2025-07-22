import numpy as np
from filter.confidence import compute_confidence


def test_confidence_drops_with_high_variance():
    cov = np.array([[1000, 0], [0, 1000]])
    confidence = compute_confidence(cov)
    assert confidence < 0.01


def test_confidence_high_with_low_variance():
    cov = np.array([[0.01, 0], [0, 0.01]])
    confidence = compute_confidence(cov)
    assert confidence > 0.99
