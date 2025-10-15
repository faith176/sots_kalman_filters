import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuration
BASE_DIR = "data/logs/experiment_example/20251015-192544"  # ← change to your actual run directory
DATASETS = ["oracle", "mnar_30"]
EVENT_FILE = "events.csv"
PATTERN_FILE = "patterns.csv"
TIME_TOLERANCE_SEC = 3   # how close a match in seconds counts as same detection

# ---------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------
def safe_load_csv(path):
    if not os.path.exists(path):
        print(f"[WARN] Missing file: {path}")
        return pd.DataFrame()
    try:
        return pd.read_csv(path, comment="#") 
    except Exception as e:
        print(f"[ERROR] Failed to load {path}: {e}")
        return pd.DataFrame()


def parse_ts(ts):
    if pd.isna(ts):
        return None
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(float(ts))
        except Exception:
            return None
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(str(ts), fmt)
        except Exception:
            continue
    return None

# ---------------------------------------------------------------------
# 1️⃣ Event-level reconstruction accuracy
# ---------------------------------------------------------------------
def evaluate_reconstruction(df):
    if df.empty:
        return pd.DataFrame()
    
    metrics = []
    for beach in sorted({b.split("_")[0] for b in df["stream_id"].unique()}):
        beach_df = df[df["stream_id"].str.startswith(beach)]
        for attr in ["Water_Temperature", "Turbidity", "Wave_Height", "Wave_Period"]:
            sub = beach_df[beach_df["stream_id"].str.contains(attr)]
            if sub.empty:
                continue
            sub = sub.copy()
            gt = sub["extras"].astype(str).str.extract(r"'ground_truth': ([0-9.\-eE]+)")[0].astype(float)
            pred = sub["reconstructed_value"].astype(float)
            conf = sub["confidence"].astype(float)
            mae = np.mean(np.abs(pred - gt))
            rmse = np.sqrt(np.mean((pred - gt) ** 2))
            metrics.append({
                "beach": beach,
                "attribute": attr,
                "MAE": mae,
                "RMSE": rmse,
                "avg_confidence": np.mean(conf)
            })
    return pd.DataFrame(metrics)

# ---------------------------------------------------------------------
# 2️⃣ Pattern-level match vs oracle
# ---------------------------------------------------------------------
def compare_patterns(oracle_df, exp_df, tolerance_s=10):
    if oracle_df.empty or exp_df.empty:
        return pd.DataFrame(columns=["pattern_name", "TP", "FP", "FN"])
    
    oracle_df["fired_at_dt"] = oracle_df["fired_at"].apply(parse_ts)
    exp_df["fired_at_dt"] = exp_df["fired_at"].apply(parse_ts)
    
    results = []
    for pattern in sorted(oracle_df["pattern_name"].unique()):
        o_sub = oracle_df[oracle_df["pattern_name"] == pattern]
        e_sub = exp_df[exp_df["pattern_name"] == pattern]

        tp = 0
        matched = set()
        for _, o_row in o_sub.iterrows():
            o_time = o_row["fired_at_dt"]
            if o_time is None:
                continue
            # Find closest experimental match
            diffs = e_sub["fired_at_dt"].apply(lambda t: abs((t - o_time).total_seconds()) if t else np.inf)
            if not diffs.empty and diffs.min() <= tolerance_s:
                tp += 1
                matched.add(diffs.idxmin())

        fp = len(e_sub) - len(matched)
        fn = len(o_sub) - tp
        results.append({
            "pattern_name": pattern,
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "precision": tp / (tp + fp) if (tp + fp) > 0 else 0,
            "recall": tp / (tp + fn) if (tp + fn) > 0 else 0
        })

    return pd.DataFrame(results)

# ---------------------------------------------------------------------
# 🧾 Main evaluation pipeline
# ---------------------------------------------------------------------
def main():
    oracle_events = safe_load_csv(os.path.join(BASE_DIR, "oracle", EVENT_FILE))
    oracle_patterns = safe_load_csv(os.path.join(BASE_DIR, "oracle", PATTERN_FILE))
    
    all_recon = []
    all_patterns = []
    
    for dataset in DATASETS:
        print(f"\n[INFO] Evaluating {dataset}...")
        ds_dir = os.path.join(BASE_DIR, dataset)
        if not os.path.exists(ds_dir):
            print(f"[WARN] Skipping missing dataset {dataset}")
            continue
        
        events_path = os.path.join(ds_dir, EVENT_FILE)
        patterns_path = os.path.join(ds_dir, PATTERN_FILE)
        df_events = safe_load_csv(events_path)
        df_patterns = safe_load_csv(patterns_path)
        
        # 1️⃣ Reconstruction Metrics
        recon_df = evaluate_reconstruction(df_events)
        recon_df["dataset"] = dataset
        all_recon.append(recon_df)
        
        # 2️⃣ Pattern Match vs Oracle
        cmp_df = compare_patterns(oracle_patterns, df_patterns, tolerance_s=TIME_TOLERANCE_SEC)
        cmp_df["dataset"] = dataset
        all_patterns.append(cmp_df)
    
    # Combine and save
    out_dir = os.path.join(BASE_DIR, "evaluation_results")
    os.makedirs(out_dir, exist_ok=True)
    
    recon_all = pd.concat(all_recon, ignore_index=True)
    pattern_all = pd.concat(all_patterns, ignore_index=True)
    
    recon_all.to_csv(os.path.join(out_dir, "reconstruction_metrics.csv"), index=False)
    pattern_all.to_csv(os.path.join(out_dir, "pattern_comparison.csv"), index=False)
    
    print(f"[INFO] Exported results to {out_dir}")
    print(f"\n=== Reconstruction Metrics ===\n{recon_all.groupby('dataset')[['MAE','RMSE','avg_confidence']].mean()}")
    print(f"\n=== Pattern Match Summary ===\n{pattern_all.groupby('dataset')[['precision','recall']].mean()}")

if __name__ == "__main__":
    main()
