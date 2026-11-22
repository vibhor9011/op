"""Phase 2: Target engineering for flood extent regression and threshold classification."""

import numpy as np
import pandas as pd

GRANULARITY_CONFIG = {
    "temporal_granularity": "month",
    "primary_cls_threshold": 0.02,
    "sensitivity_thresholds": [0.01, 0.05],
    "clip_percentile": 99.5
}


def compute_targets(df_train: pd.DataFrame, df_test: pd.DataFrame = None, target_col: str = "flood_frac_valid") -> dict:
    """
    Compute T_reg (clipped at training 99.5th percentile) and T_cls (>= 0.02).
    Also attaches sensitivity targets for 0.01 and 0.05.
    """
    res = {}
    train_vals = df_train[target_col].dropna()
    if len(train_vals) > 0:
        clip_val = float(np.percentile(train_vals, GRANULARITY_CONFIG["clip_percentile"]))
    else:
        clip_val = 1.0

    res["clip_threshold_99_5"] = clip_val

    # Training targets
    y_reg_tr = np.clip(df_train[target_col], 0.0, clip_val)
    y_cls_tr = (df_train[target_col] >= GRANULARITY_CONFIG["primary_cls_threshold"]).astype(int)
    y_cls_01_tr = (df_train[target_col] >= 0.01).astype(int)
    y_cls_05_tr = (df_train[target_col] >= 0.05).astype(int)

    res["train"] = {
        "T_reg": y_reg_tr,
        "T_cls": y_cls_tr,
        "T_cls_01": y_cls_01_tr,
        "T_cls_05": y_cls_05_tr
    }

    # Test targets
    if df_test is not None:
        y_reg_te = np.clip(df_test[target_col], 0.0, clip_val)
        y_cls_te = (df_test[target_col] >= GRANULARITY_CONFIG["primary_cls_threshold"]).astype(int)
        y_cls_01_te = (df_test[target_col] >= 0.01).astype(int)
        y_cls_05_te = (df_test[target_col] >= 0.05).astype(int)

        res["test"] = {
            "T_reg": y_reg_te,
            "T_cls": y_cls_te,
            "T_cls_01": y_cls_01_te,
            "T_cls_05": y_cls_05_te
        }

    return res
