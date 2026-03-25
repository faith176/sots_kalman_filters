import numpy as np
from scipy.stats import spearmanr
from app.core.compensator.predictor_types.Filters import KalmanFilter


def simulate_measurements(n=15, mean=10, std=7, seed=42):
    np.random.seed(seed)
    return np.random.normal(mean, std, n)


def run_experiment(Q, R, alpha, std, verbose=False):
    measurements = simulate_measurements(std=std)

    initial_estimate = measurements[0] + np.random.normal(0, 5)

    predictor = KalmanFilter(
        Q=Q,
        R=R,
        dt=1.0,
        mode="position",
        initial_value=initial_estimate
    )

    predictor.alpha = alpha

    missing_pattern = [False, False, True, False, True]

    errors = []
    confidences = []

    for t in range(len(measurements)):
        z = measurements[t]
        is_missing = missing_pattern[t % len(missing_pattern)]

        # --- Always get prediction first ---
        pred = predictor.predict()
        est_prior = predictor.kf.x[0, 0]

        if is_missing:
            # No measurement
            c = predictor.confidence()

            if verbose:
                print(
                    f"{t:3d} | MISSING | "
                    f"pred={pred:.2f} | "
                    f"conf={c:.3f}"
                )

        else:
            # --- Confidence BEFORE update ---
            c = predictor.confidence(observed_value=z)

            err = abs(est_prior - z)

            errors.append(err)
            confidences.append(c)

            # --- Now update ---
            est_post = predictor.update(z)

            if verbose:
                print(
                    f"{t:3d} | z={z:.2f} | "
                    f"pred={pred:.2f} | "
                    f"prior={est_prior:.2f} | "
                    f"post={est_post:.2f} | "
                    f"err={err:.2f} | "
                    f"conf={c:.3f}"
                )

    # --- Metrics ---
    errors = np.array(errors)
    confidences = np.array(confidences)

    pearson = np.corrcoef(errors, confidences)[0, 1]
    spearman = spearmanr(errors, confidences).correlation

    results = {
        "pearson": pearson,
        "spearman": spearman,
        "error_mean": np.mean(errors),
        "error_max": np.max(errors),
        "error_min": np.min(errors),
        "conf_mean": np.mean(confidences),
        "conf_max": np.max(confidences),
        "conf_min": np.min(confidences),
    }

    return results


def run_experiment_missing(Q, R, alpha, std, missing_steps=15, verbose=False):
    measurements = simulate_measurements(std=std)

    initial_estimate = measurements[0] + np.random.normal(0, 5)

    predictor = KalmanFilter(
        Q=Q,
        R=R,
        dt=1.0,
        mode="position",
        initial_value=initial_estimate
    )

    predictor.alpha = alpha

    # --- Warmup phase (FIXED ORDER) ---
    for z in measurements[:50]:
        predictor.confidence(z)   # BEFORE update
        predictor.update(z)

    # --- Missing phase ---
    confidences = []

    for t in range(missing_steps):
        predictor.predict()
        c = predictor.confidence()

        confidences.append(c)

        if verbose:
            est = predictor.kf.x[0, 0]
            print(f"{t:2d} | MISSING | est={est:.2f} | c={c:.3f}")

    confidences = np.array(confidences)

    results = {
        "start_conf": confidences[0],
        "end_conf": confidences[-1],
        "drop": confidences[0] - confidences[-1],
        "steps_to_80": np.argmax(confidences < 0.8) if np.any(confidences < 0.8) else -1,
        "steps_to_60": np.argmax(confidences < 0.6) if np.any(confidences < 0.6) else -1,
        "steps_to_40": np.argmax(confidences < 0.4) if np.any(confidences < 0.4) else -1,
    }

    return results, confidences


def main():
    Q_values = [0.001, 0.01, 0.1, 1.0,]
    R_values = [5, 10, 25,]
    alpha_values = [0.1, 0.2, 0.3]
    std_values = [0.5, 1, 3, 7]

    print("\n==== CONFIDENCE VALIDATION ====\n")

    for std in std_values:
        print(f"\n### Noise STD = {std}")
        print("-" * 50)

        for Q in Q_values:
            for R in R_values:
                for alpha in alpha_values:
                    res = run_experiment(Q, R, alpha, std, verbose=True)

                    print(
                        f"Q={Q:<4} R={R:<3} α={alpha:<3} | "
                        f"corr={res['pearson']:.3f} | "
                        f"rank={res['spearman']:.3f} | "
                        f"err μ={res['error_mean']:.2f} max={res['error_max']:.2f} | "
                        f"conf μ={res['conf_mean']:.3f} [{res['conf_min']:.3f},{res['conf_max']:.3f}]"
                    )

    print("\n==== MISSING DATA DECAY (ALPHA VALIDATION) ====\n")

    missing_steps = 15

    for Q in [0.01, 0.1]:
        for R in [50, 150]:
            for alpha in alpha_values:

                res, _ = run_experiment_missing(Q, R, alpha, std=1, missing_steps=missing_steps)

                print(
                    f"Q={Q:<4} R={R:<3} α={alpha:<3} | "
                    f"start={res['start_conf']:.3f} → end={res['end_conf']:.3f} | "
                    f"drop={res['drop']:.3f} | "
                    f"t<0.8={res['steps_to_80']} "
                    f"t<0.6={res['steps_to_60']} "
                    f"t<0.4={res['steps_to_40']}"
                )


if __name__ == "__main__":
    main()