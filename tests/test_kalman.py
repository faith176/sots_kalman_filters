import numpy as np
from app.core.compensator.predictor_types.Filters import KalmanFilter
import matplotlib.pyplot as plt

def generate_signal(n=500, seed=42):
    np.random.seed(seed)
    t = np.arange(n)

    signal = (
        0.05 * t +
        2 * np.sin(0.05 * t) +
        np.random.normal(0, 0.5, n)
    )

    return t, signal


def apply_missing(signal, drop_prob=0.3, seed=42):
    np.random.seed(seed)

    observed = signal.copy()
    mask = np.random.rand(len(signal)) < drop_prob

    observed[mask] = np.nan
    return observed, mask

def run_filter(observed):
    kf = KalmanFilter(
        dt=1.0,
        Q=0.01,
        R=0.5,
        mode="acceleration"
    )

    estimates = []
    confidences = []
    uncertainties = []

    for z in observed:
        pred = kf.predict()

        if np.isnan(z):
            est = pred
            conf = kf.confidence(None)
        else:
            est = kf.update(z)
            conf = kf.confidence(z)

        estimates.append(est)
        confidences.append(conf)
        uncertainties.append(np.trace(kf.kf.P))

    return (
        np.array(estimates),
        np.array(confidences),
        np.array(uncertainties)
    )


def compute_metrics(gt, estimates, mask, confidences):
    idx = mask  # reconstructed only

    errors = estimates[idx] - gt[idx]
    abs_errors = np.abs(errors)

    mae = np.mean(abs_errors)
    rmse = np.sqrt(np.mean(errors**2))

    conf = confidences[idx]

    # Correlation (confidence vs error)
    if len(conf) > 1:
        corr = np.corrcoef(conf, abs_errors)[0, 1]
    else:
        corr = np.nan

    return {
        "mae": mae,
        "rmse": rmse,
        "conf_mean": np.mean(conf),
        "conf_min": np.min(conf),
        "conf_max": np.max(conf),
        "conf_error_corr": corr,
    }


def plot_all(t, gt, observed, estimates, confidences, uncertainties):
    plt.figure(figsize=(14, 10))

    # Signal
    plt.subplot(3, 1, 1)
    plt.plot(t, gt, label="Ground Truth", linewidth=2)
    plt.scatter(t, observed, label="Observed", s=10)
    plt.plot(t, estimates, label="Estimate", linestyle="--")
    plt.legend()
    plt.title("Signal Reconstruction")

    # Confidence
    plt.subplot(3, 1, 2)
    plt.plot(t, confidences, label="Confidence")
    plt.title("Confidence Over Time")
    plt.legend()

    # Uncertainty
    plt.subplot(3, 1, 3)
    plt.plot(t, uncertainties, label="Trace(P)")
    plt.title("Uncertainty Growth")
    plt.legend()

    plt.tight_layout()
    plt.show()


def main():
    t, gt = generate_signal()
    observed, mask = apply_missing(gt, drop_prob=0.3)

    estimates, confidences, uncertainties = run_filter(observed)

    metrics = compute_metrics(gt, estimates, mask, confidences)

    print("\n===== KALMAN TEST =====")
    for k, v in metrics.items():
        print(f"{k}: {v:.4f}")

    plot_all(t, gt, observed, estimates, confidences, uncertainties)


if __name__ == "__main__":
    main()