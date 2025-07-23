 
import numpy as np

def compute_confidence(cov_matrix):
    variance = cov_matrix[0, 0]
    confidence = 1.0 / (1.0 + variance)
    return max(0.0, min(1.0, confidence)) 