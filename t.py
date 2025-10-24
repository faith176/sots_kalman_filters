import numpy as np
import matplotlib.pyplot as plt
from app.core.reconstruction.predictor_types.Filters import KalmanFilter

# -------------------------------
# 1. Generate synthetic data
# -------------------------------
np.random.seed(42)
n_steps = 1000
t = np.arange(n_steps)
true_values = np.sin(0.05 * t) + 0.2 * np.sin(0.25 * t)
observed = true_values + np.random.normal(0, 0.05, size=n_steps)

# Introduce missing data (30%)
missing_mask = np.random.rand(n_steps) < 0.3
observed_with_gaps = observed.copy()
observed_with_gaps[missing_mask] = np.nan

# -------------------------------
# 2. Initialize filter
# -------------------------------
kf = KalmanFilter(dt=1.0, Q=0.02, R=0.01, initial_value=0.0, mode="position", alpha=0.3)

predictions = []
confidences = []
errors = []

# -------------------------------
# 3. Run simulation
# -------------------------------
for i in range(n_steps):
    # Predict step
    pred = kf.predict()
    predictions.append(pred)

    # If measurement available, update
    if not np.isnan(observed_with_gaps[i]):
        kf.update(observed_with_gaps[i])
        conf = kf.confidence(observed_value=observed_with_gaps[i])
    else:
        conf = kf.confidence()  # no measurement -> decay

    confidences.append(conf)
    errors.append(abs(pred - true_values[i]))
    # print(f"Error: {pred - true_values[i]} Condidence: {conf}")

# Convert to arrays for plotting
predictions = np.array(predictions)
confidences = np.array(confidences)
errors = np.array(errors)

# -------------------------------
# 4. Plot confidence over time
# -------------------------------
plt.figure(figsize=(10, 5))
plt.plot(t, confidences, label="Hybrid Confidence", lw=2, color="#1f77b4")

# Identify contiguous missing segments
in_gap = False
gap_start = None
for i in range(n_steps):
    if missing_mask[i] and not in_gap:
        in_gap = True
        gap_start = i
    elif not missing_mask[i] and in_gap:
        in_gap = False
        plt.axvspan(gap_start, i, color="red", alpha=0.12)
# handle gap ending at the end of series
if in_gap:
    plt.axvspan(gap_start, n_steps, color="red", alpha=0.12)

plt.title("Confidence Over Time (Shaded = Missing Measurements)")
plt.xlabel("Time step")
plt.ylabel("Confidence")
plt.ylim(0, 1.05)
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

# -------------------------------
# 5. Plot MAE vs Confidence
# -------------------------------
plt.figure(figsize=(6, 5))
plt.scatter(confidences, errors, alpha=0.7)
z = np.polyfit(confidences, errors, 1)
p = np.poly1d(z)
plt.plot(confidences, p(confidences), "r--",
         label=f"Linear fit (slope={z[0]:.3f})")
plt.xlabel("Confidence")
plt.ylabel("Absolute Error (|prediction - truth|)")
plt.title("Inverse Relationship Between Confidence and MAE")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.show()





alphas = np.linspace(0.3, 1.2, 20)
corrs = []

for a in alphas:
    kf.alpha = a
    confs, errs = [], []

    for i in range(n_steps):
        pred = kf.predict()
        if not np.isnan(observed_with_gaps[i]):
            kf.update(observed_with_gaps[i])
            conf = kf.confidence(observed_value=observed_with_gaps[i])
        else:
            conf = kf.confidence()
        confs.append(conf)
        errs.append(abs(pred - true_values[i]))

    r = np.corrcoef(confs, errs)[0, 1]  # negative correlation expected
    corrs.append(r)

best_alpha = alphas[np.argmin(corrs)]  # most negative correlation
print(f"Optimal α ≈ {best_alpha:.2f}, correlation = {min(corrs):.3f}")


import numpy as np
import matplotlib.pyplot as plt

norm_innov = np.linspace(0, 4, 400)
NIS = norm_innov ** 2
confidence = np.exp(-0.5 * norm_innov)
gaussian_likelihood = np.exp(-0.5 * NIS)
normalized_NIS = NIS / np.max(NIS)

plt.figure(figsize=(8, 5))
plt.plot(norm_innov, gaussian_likelihood, '--', label="Gaussian Likelihood (exp(-0.5·NIS))", lw=2)
plt.plot(norm_innov, normalized_NIS, ':', label="Normalized NIS (scaled)", lw=2)

# Add σ-level markers
for sigma in [1, 2, 3]:
    c_val = np.exp(-0.5 * sigma)
    plt.axvline(sigma, color='gray', ls='--', lw=0.8)
    plt.text(sigma + 0.05, c_val + 0.03, f"{sigma}σ\nc={c_val:.2f}", fontsize=8)

plt.xlabel("Normalized innovation magnitude  |v| / √S")
plt.ylabel("Value (normalized scale)")
plt.title("Relationship Between NIS and Proposed Confidence Metric")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()
