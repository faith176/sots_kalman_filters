 
import numpy as np

def compute_confidence(cov_matrix):
    if cov_matrix.shape[0] < 1 or cov_matrix.shape[1] < 1:
        raise ValueError("Covariance matrix is empty or malformed.")

    variance = cov_matrix[0, 0]
    confidence = 1.0 / (1.0 + variance)
    return max(0.0, min(1.0, confidence)) 