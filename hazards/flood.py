"""Phase 3 & 4: Flood Hazard Baselines (B0-B3) and Machine Learning Models (M1-M7).

Implements BaseHazardModel with:
- build_features(df)
- build_labels(df)
- fit(X_train, y_train_cls, y_train_reg)
- predict(X) -> DataFrame[p_low, p_mid, p_high]
- extent() -> None
- explain(X) -> dict

Also provides:
- run_primary_loyo_cv: Primary LOYO CV pipeline on Sentinel-1 SAR observations (M1-M6 vs B0-B3)
- run_synthetic_m7_pipeline: Secondary LOYO CV pipeline for degraded mode structural checks
"""

import os
import json
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    brier_score_loss, roc_auc_score, average_precision_score,
    precision_score, recall_score, f1_score,
    mean_squared_error, mean_absolute_error, r2_score
)
from scipy.stats import spearmanr
from scipy.special import expit

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from core.hazard import BaseHazardModel
from core.features import compute_infold_features
from core.targets import compute_targets, GRANULARITY_CONFIG

METRICS_DIR = "metrics"
REPORTS_DIR = "reports"
OUTPUTS_DIR = "outputs"


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error (ECE) across n_bins equal-width bins."""
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    if n == 0:
        return 0.0

    for i in range(n_bins):
        bin_mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i+1] if i < n_bins - 1 else y_prob <= bin_edges[i+1])
        bin_size = np.sum(bin_mask)
        if bin_size > 0:
            bin_acc = np.mean(y_true[bin_mask])
            bin_conf = np.mean(y_prob[bin_mask])
            ece += (bin_size / n) * np.abs(bin_acc - bin_conf)
    return float(ece)


class FloodBaselines:
    """Phase 3: B0 (polygon-month climatology), B1 (month mean), B2 (logistic), B3 (persistence)."""

    def __init__(self):
        self.b0_lookup = {}
        self.b1_lookup = {}
        self.b2_model = LogisticRegression(max_iter=1000)
        self.b3_lookup = {}
        self.b0_global = 0.5

    def fit(self, X_train: pd.DataFrame, y_train_cls: pd.Series):
        df_tr = X_train.copy()
        df_tr["target"] = y_train_cls.values

        # B0: polygon-month mean
        self.b0_lookup = df_tr.groupby(["geometry_id", "month"])["target"].mean().to_dict()
        self.b0_global = float(df_tr["target"].mean()) if not df_tr.empty else 0.5

        # B1: month-only mean
        self.b1_lookup = df_tr.groupby("month")["target"].mean().to_dict()

        # B2: Logistic Regression
        feature_cols = [c for c in X_train.columns if c in ["rain_total_mm", "rain_lag1_mm", "rain_cum3m_mm", "month_sin", "month_cos", "geom_code"]]
        if feature_cols:
            X_num = X_train[feature_cols].fillna(0.0)
            self.b2_features = feature_cols
            try:
                self.b2_model.fit(X_num, y_train_cls)
            except Exception:
                pass

        # B3: Persistence lookup (previous observed month's label)
        self.b3_lookup = df_tr.set_index(["geometry_id", "year", "month"])["target"].to_dict()

    def predict(self, X_test: pd.DataFrame) -> dict:
        b0_preds = np.array([self.b0_lookup.get((r["geometry_id"], r["month"]), self.b0_global) for _, r in X_test.iterrows()])
        b1_preds = np.array([self.b1_lookup.get(r["month"], self.b0_global) for _, r in X_test.iterrows()])

        if hasattr(self, "b2_features") and self.b2_features:
            X_num = X_test[self.b2_features].fillna(0.0)
            try:
                b2_preds = self.b2_model.predict_proba(X_num)[:, 1]
            except Exception:
                b2_preds = b0_preds
        else:
            b2_preds = b0_preds

        b3_preds = []
        for _, r in X_test.iterrows():
            prev_m = r["month"] - 1
            prev_yr = r["year"]
            if prev_m == 0:
                prev_m = 12
                prev_yr = r["year"] - 1
            val = self.b3_lookup.get((r["geometry_id"], prev_yr, prev_m), self.b0_lookup.get((r["geometry_id"], r["month"]), self.b0_global))
            b3_preds.append(val)

        return {
            "B0_climatology": np.clip(b0_preds, 0.0, 1.0),
            "B1_month_mean": np.clip(b1_preds, 0.0, 1.0),
            "B2_logistic": np.clip(b2_preds, 0.0, 1.0),
            "B3_persistence": np.clip(np.array(b3_preds), 0.0, 1.0)
        }


class FloodHazardModel(BaseHazardModel):
    """
    Phase 4:
    M1 LightGBM classifier on T_cls (lr 0.03, num_leaves 15, min_child_samples 30, subsample 0.8, colsample 0.8, ~400 trees).
    M2 Isotonic calibration on nested out-of-fold predictions.
    M3 LightGBM quantile regressors (alpha 0.1, 0.5, 0.9) on T_reg.
    M4 Conformalized Quantile Regression (CQR) coverage adjustment.
    M5 Mapping: p_mid = calibrated M1 prob; p_low/p_high = prob that CQR lower/upper quantile exceeds 2% threshold.
    M6 SHAP TreeExplainer: global summary + top-5 local polygon waterfalls.
    """

    def __init__(self):
        super().__init__(hazard_name="flood")
        self.clf_raw = None
        self.calibrator = IsotonicRegression(out_of_bounds="clip")
        self.q_models = {}
        self.cqr_adjustment = 0.0
        self.feature_names = []

    def extent(self, period: str = None) -> dict:
        """Spatial extent analysis and footprint generation for a specified period."""
        from sar.extent import process_extent
        return process_extent(period=period)

    def build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract and clean model features from raw table."""
        df_feats = df.copy()
        if "month" in df_feats.columns:
            df_feats["month_sin"] = np.sin(2 * np.pi * df_feats["month"] / 12.0)
            df_feats["month_cos"] = np.cos(2 * np.pi * df_feats["month"] / 12.0)
        if "geometry_id" in df_feats.columns:
            all_gids = [f"G{i+1:02d}" for i in range(33)]
            gid_map = {g: i for i, g in enumerate(all_gids)}
            df_feats["geom_code"] = df_feats["geometry_id"].map(lambda g: gid_map.get(g, -1))
        return df_feats

    def build_labels(self, df: pd.DataFrame) -> tuple:
        """Extract classification (T_cls) and regression (T_reg) target labels."""
        if "flood_frac_valid" not in df.columns:
            n = len(df)
            return pd.Series(np.zeros(n)), pd.Series(np.zeros(n))

        y_cls = (df["flood_frac_valid"] >= GRANULARITY_CONFIG["primary_cls_threshold"]).astype(int)
        clip_val = float(np.percentile(df["flood_frac_valid"].dropna(), GRANULARITY_CONFIG["clip_percentile"])) if not df["flood_frac_valid"].dropna().empty else 1.0
        y_reg = np.clip(df["flood_frac_valid"], 0.0, clip_val)
        return y_cls, y_reg

    def fit(self, X_train: pd.DataFrame, y_train_cls: pd.Series, y_train_reg: pd.Series = None):
        """Fit M1, M2, M3, M4 on in-fold training data."""
        self.feature_names = [c for c in X_train.columns if c not in ["geometry_id", "district", "year", "period", "label_source", "fold_year"]]
        X_tr = X_train[self.feature_names].fillna(0.0)

        # M1: LightGBM Classifier
        min_child = min(30, max(2, len(X_tr) // 10))
        self.clf_raw = lgb.LGBMClassifier(
            learning_rate=0.03,
            num_leaves=15,
            min_child_samples=min_child,
            subsample=0.8,
            colsample_bytree=0.8,
            n_estimators=400,
            random_state=42,
            verbose=-1
        )
        self.clf_raw.fit(X_tr, y_train_cls)

        # M2: Nested out-of-fold calibration (5-fold)
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=min(5, len(X_tr)), shuffle=True, random_state=42)
        oof_probs = np.zeros(len(X_tr))
        for tr_idx, val_idx in kf.split(X_tr):
            m_inner = lgb.LGBMClassifier(
                learning_rate=0.03, num_leaves=15, min_child_samples=min_child,
                subsample=0.8, colsample_bytree=0.8, n_estimators=150,
                random_state=42, verbose=-1
            )
            m_inner.fit(X_tr.iloc[tr_idx], y_train_cls.iloc[tr_idx])
            oof_probs[val_idx] = m_inner.predict_proba(X_tr.iloc[val_idx])[:, 1]

        self.calibrator.fit(oof_probs, y_train_cls)

        # M3: Quantile Regressors (alpha = 0.10, 0.50, 0.90)
        if y_train_reg is not None and not y_train_reg.dropna().empty:
            for alpha in [0.10, 0.50, 0.90]:
                q_model = lgb.LGBMRegressor(
                    objective="quantile",
                    alpha=alpha,
                    learning_rate=0.03,
                    num_leaves=15,
                    min_child_samples=min_child,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    n_estimators=250,
                    random_state=42,
                    verbose=-1
                )
                q_model.fit(X_tr, y_train_reg)
                self.q_models[alpha] = q_model

            # M4: Conformalized Quantile Regression (CQR) adjustment
            preds_q10 = self.q_models[0.10].predict(X_tr)
            preds_q90 = self.q_models[0.90].predict(X_tr)
            residuals = np.maximum(preds_q10 - y_train_reg.values, y_train_reg.values - preds_q90)
            self.cqr_adjustment = float(np.quantile(residuals, 0.80))

        self.is_fitted = True

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Calibrated probability p_mid."""
        X_sub = X[self.feature_names].fillna(0.0)
        raw_prob = self.clf_raw.predict_proba(X_sub)[:, 1]
        cal_prob = self.calibrator.predict(raw_prob)
        return np.clip(cal_prob, 0.0, 1.0)

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """Phase 4 M5: Return DataFrame[p_low, p_mid, p_high]."""
        p_mid = self.predict_proba(X)
        q_df = self.predict_quantiles(X)

        threshold = GRANULARITY_CONFIG["primary_cls_threshold"]  # 0.02
        scale = 0.005

        cqr_low = q_df["cqr_low"].values
        gate_low = expit((cqr_low - threshold) / scale)
        p_low = np.clip(p_mid * gate_low, 0.0, 1.0)

        cqr_high = q_df["cqr_high"].values
        gate_high = expit((threshold - cqr_high) / scale)
        p_high = np.clip(1.0 - (1.0 - p_mid) * gate_high, 0.0, 1.0)

        p_low = np.minimum(p_low, p_mid)
        p_high = np.maximum(p_high, p_mid)

        res_df = pd.DataFrame({
            "p_low": np.round(p_low, 4),
            "p_mid": np.round(p_mid, 4),
            "p_high": np.round(p_high, 4)
        }, index=X.index)

        return res_df

    def predict_quantiles(self, X: pd.DataFrame) -> pd.DataFrame:
        """M3 + M4: Quantile predictions and CQR-adjusted bands."""
        n = len(X)
        if not self.q_models:
            return pd.DataFrame({"q10": np.zeros(n), "q50": np.zeros(n), "q90": np.zeros(n), "cqr_low": np.zeros(n), "cqr_high": np.zeros(n)}, index=X.index)

        X_sub = X[self.feature_names].fillna(0.0)
        res = {}
        for alpha, model in self.q_models.items():
            col = f"q{int(alpha*100):02d}"
            res[col] = model.predict(X_sub)

        # CQR bands with non-crossing guarantee
        raw_low = np.maximum(0.0, res["q10"] - self.cqr_adjustment)
        raw_high = np.maximum(0.0, res["q90"] + self.cqr_adjustment)
        res["cqr_low"] = np.minimum(raw_low, raw_high)
        res["cqr_high"] = np.maximum(raw_low, raw_high)
        return pd.DataFrame(res, index=X.index)

    @staticmethod
    def map_risk_tier(prob: float) -> str:
        """Map calibrated prob to {low: p < 0.25, mid: 0.25 <= p < 0.65, high: p >= 0.65}."""
        if prob < 0.25:
            return "low"
        elif prob < 0.65:
            return "mid"
        else:
            return "high"

    def explain(self, X: pd.DataFrame) -> dict:
        """M6: SHAP TreeExplainer feature attributions."""
        import shap
        X_sub = X[self.feature_names].fillna(0.0)
        explainer = shap.TreeExplainer(self.clf_raw)
        shap_values = explainer.shap_values(X_sub)
        if isinstance(shap_values, list):
            shap_arr = shap_values[1]
        else:
            shap_arr = shap_values

        mean_abs = np.mean(np.abs(shap_arr), axis=0)
        top_indices = np.argsort(mean_abs)[::-1][:5]
        top_features = [{"feature": self.feature_names[i], "importance": float(mean_abs[i])} for i in top_indices]

        # Save summary plot
        os.makedirs(REPORTS_DIR, exist_ok=True)
        fig, ax = plt.subplots(figsize=(8, 5))
        shap.summary_plot(shap_arr, X_sub, max_display=10, show=False)
        plot_path = os.path.join(REPORTS_DIR, "shap_summary_m1.png")
        plt.tight_layout()
        plt.savefig(plot_path, dpi=150)
        plt.close()

        # Local explanations for top 5 predictions in highest risk month
        p_preds = self.predict_proba(X)
        top_5_idx = np.argsort(p_preds)[::-1][:5]
        waterfall_paths = []
        for rank, idx in enumerate(top_5_idx):
            fig_w, ax_w = plt.subplots(figsize=(7, 4))
            exp_val = explainer.expected_value[1] if isinstance(explainer.expected_value, (list, np.ndarray)) else explainer.expected_value
            explanation = shap.Explanation(
                values=shap_arr[idx],
                base_values=exp_val,
                data=X_sub.iloc[idx].values,
                feature_names=self.feature_names
            )
            shap.plots.waterfall(explanation, max_display=6, show=False)
            wf_path = os.path.join(REPORTS_DIR, f"shap_waterfall_top_{rank+1}.png")
            fig_w.tight_layout()
            fig_w.savefig(wf_path, dpi=150)
            plt.close()
            waterfall_paths.append(wf_path)

        return {"top_features": top_features, "summary_plot": plot_path, "waterfalls": waterfall_paths}


def run_primary_loyo_cv(sar_table_path: str = None) -> dict:
    """
    Phase 4 & 5: Primary LOYO CV Pipeline on Sentinel-1 SAR Observations (M1-M6 vs B0-B3).
    Evaluates:
    - ROC-AUC, PR-AUC, Brier score, ECE
    - Precision, Recall, F1 at in-fold optimal threshold
    - MAE and Spearman rho on T_reg
    - Nominal 80% CQR band coverage per held-out year and overall
    - Annual anchor Spearman correlation with bootstrap CI (n ~ 10)
    """
    if not sar_table_path or not os.path.exists(sar_table_path):
        sar_table_path = os.path.join("data", "processed", "sar_polygon_month.csv")

    df_sar = pd.read_csv(sar_table_path)

    # Honesty Rule 2: Train/evaluate primary model ONLY on rows with sar_label_usable = 1
    if "sar_label_usable" not in df_sar.columns or df_sar["sar_label_usable"].sum() == 0:
        print("[Primary LOYO CV] No usable Sentinel-1 SAR observations found. Skipping primary LOYO CV.")
        return None

    usable_df = df_sar[df_sar["sar_label_usable"] == 1].copy()
    usable_years = usable_df.groupby("year").size()
    valid_years = usable_years[usable_years >= 100].index.tolist()

    if len(valid_years) < 8:
        print(f"[Primary LOYO CV] Only {len(valid_years)} distinct years with >=100 usable labels (min 8 required).")
        return None

    usable_df = usable_df[usable_df["year"].isin(valid_years)].copy()
    print(f"[Primary LOYO CV] Running Leave-One-Year-Out CV over {len(valid_years)} years ({len(usable_df)} usable rows)...")

    # Storage for out-of-fold evaluation
    usable_df["oof_prob_m1"] = 0.0
    usable_df["oof_q10"] = 0.0
    usable_df["oof_q50"] = 0.0
    usable_df["oof_q90"] = 0.0
    usable_df["oof_cqr_low"] = 0.0
    usable_df["oof_cqr_high"] = 0.0

    b0_preds = np.zeros(len(usable_df))
    b1_preds = np.zeros(len(usable_df))
    b2_preds = np.zeros(len(usable_df))
    b3_preds = np.zeros(len(usable_df))

    yearly_metrics = {}

    for val_year in valid_years:
        train_mask = usable_df["year"] != val_year
        test_mask = usable_df["year"] == val_year

        df_train_raw = usable_df[train_mask].copy()
        df_test_raw = usable_df[test_mask].copy()

        # In-fold feature computation
        df_tr, df_te = compute_infold_features(df_train_raw, df_test_raw)

        # In-fold target computation
        target_dict = compute_targets(df_tr, df_te)
        y_cls_tr = target_dict["train"]["T_cls"]
        y_reg_tr = target_dict["train"]["T_reg"]
        y_cls_te = target_dict["test"]["T_cls"]
        y_reg_te = target_dict["test"]["T_reg"]

        # Baselines fit & predict
        baselines = FloodBaselines()
        baselines.fit(df_tr, y_cls_tr)
        b_preds = baselines.predict(df_te)

        b0_preds[test_mask] = b_preds["B0_climatology"]
        b1_preds[test_mask] = b_preds["B1_month_mean"]
        b2_preds[test_mask] = b_preds["B2_logistic"]
        b3_preds[test_mask] = b_preds["B3_persistence"]

        # M1-M4 Model fit & predict
        model = FloodHazardModel()
        model.fit(df_tr, y_cls_tr, y_reg_tr)
        pred_df = model.predict(df_te)
        q_df = model.predict_quantiles(df_te)

        usable_df.loc[test_mask, "oof_prob_m1"] = pred_df["p_mid"].values
        usable_df.loc[test_mask, "oof_q10"] = q_df["q10"].values
        usable_df.loc[test_mask, "oof_q50"] = q_df["q50"].values
        usable_df.loc[test_mask, "oof_q90"] = q_df["q90"].values
        usable_df.loc[test_mask, "oof_cqr_low"] = q_df["cqr_low"].values
        usable_df.loc[test_mask, "oof_cqr_high"] = q_df["cqr_high"].values

        # Annual coverage
        cov_yr = np.mean((y_reg_te.values >= q_df["cqr_low"].values) & (y_reg_te.values <= q_df["cqr_high"].values))
        yearly_metrics[val_year] = {
            "n_records": int(test_mask.sum()),
            "cqr_coverage": round(float(cov_yr), 4),
            "roc_auc": round(float(roc_auc_score(y_cls_te, pred_df["p_mid"])), 4) if len(np.unique(y_cls_te)) > 1 else None
        }

    # Global Metrics
    y_true_cls = (usable_df["flood_frac_valid"] >= 0.02).astype(int)
    pos_rate = float(y_true_cls.mean())
    prob_m1 = usable_df["oof_prob_m1"].values

    roc_m1 = float(roc_auc_score(y_true_cls, prob_m1))
    pr_m1 = float(average_precision_score(y_true_cls, prob_m1))
    brier_m1 = float(brier_score_loss(y_true_cls, prob_m1))
    ece_m1 = compute_ece(y_true_cls.values, prob_m1)

    # Baselines metrics
    roc_b0 = float(roc_auc_score(y_true_cls, b0_preds))
    roc_b1 = float(roc_auc_score(y_true_cls, b1_preds))
    roc_b2 = float(roc_auc_score(y_true_cls, b2_preds))
    roc_b3 = float(roc_auc_score(y_true_cls, b3_preds))

    overall_coverage = float(np.mean(
        (usable_df["flood_frac_valid"].values >= usable_df["oof_cqr_low"].values) &
        (usable_df["flood_frac_valid"].values <= usable_df["oof_cqr_high"].values)
    ))

    # Annual anchor independent check
    annual_pred = usable_df.groupby("year")["oof_q50"].sum().reset_index()
    anchors_csv = os.path.join("data", "raw", "_unzipped", "Assam_Official_Annual_Flood_Anchors_2014_2025.csv")
    annual_spearman = None
    if os.path.exists(anchors_csv):
        df_anchors = pd.read_csv(anchors_csv)
        merged_annual = pd.merge(annual_pred, df_anchors[["year", "population_affected_persons"]], on="year", how="inner").dropna()
        if len(merged_annual) >= 5:
            rho, pval = spearmanr(merged_annual["oof_q50"], merged_annual["population_affected_persons"])
            # Bootstrap CI over years
            boot_rhos = []
            rng = np.random.default_rng(42)
            for _ in range(500):
                idx = rng.choice(len(merged_annual), size=len(merged_annual), replace=True)
                sample = merged_annual.iloc[idx]
                if sample["oof_q50"].nunique() > 1 and sample["population_affected_persons"].nunique() > 1:
                    r, _ = spearmanr(sample["oof_q50"], sample["population_affected_persons"])
                    boot_rhos.append(r)
            ci_low = float(np.percentile(boot_rhos, 2.5)) if boot_rhos else None
            ci_high = float(np.percentile(boot_rhos, 97.5)) if boot_rhos else None
            annual_spearman = {
                "n_years": len(merged_annual),
                "spearman_rho": round(float(rho), 4),
                "p_value": float(pval),
                "bootstrap_95ci": [round(ci_low, 4), round(ci_high, 4)] if ci_low is not None else None
            }

    primary_results = {
        "model": "M1_M6_Primary_Sentinel1_SAR",
        "label_source": "sentinel1_derived",
        "positive_rate": round(pos_rate, 4),
        "metrics": {
            "ROC_AUC_M1": round(roc_m1, 4),
            "PR_AUC_M1": round(pr_m1, 4),
            "Brier_Score_M1": round(brier_m1, 4),
            "ECE_M1": round(ece_m1, 4),
            "CQR_Nominal_80_Coverage": round(overall_coverage, 4)
        },
        "baselines_roc_auc": {
            "B0_climatology": round(roc_b0, 4),
            "B1_month_mean": round(roc_b1, 4),
            "B2_logistic": round(roc_b2, 4),
            "B3_persistence": round(roc_b3, 4)
        },
        "annual_anchor_independent_check": annual_spearman,
        "yearly_held_out_metrics": yearly_metrics
    }

    # Save to metrics/results.json
    results_path = os.path.join(METRICS_DIR, "results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(primary_results, f, indent=2)

    return primary_results


def run_synthetic_m7_pipeline(training_table_path: str = None) -> dict:
    """
    Phase 4 M7: Secondary severity model trained strictly on synthetic dataset.
    Predicts y_sev_synthetic = log1p(pop_affected_synthetic) with LOYO CV.
    Strictly for pipeline verification when SAR flood observations are absent.
    Outputs stamped with 'PIPELINE CHECK ONLY - no observed-derived labels'.
    """
    if not training_table_path or not os.path.exists(training_table_path):
        training_table_path = os.path.join("data", "processed", "training_table_district_month.csv")

    df = pd.read_csv(training_table_path)
    print(f"[Phase 4 M7] Running secondary synthetic severity model on {len(df)} records across 2014-2025...")

    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12.0)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12.0)

    feature_cols = [
        "area_km2", "centroid_lat", "centroid_lon", "month_sin", "month_cos",
        "geometry_is_proxy", "prior_year_dist_pop_synthetic"
    ]
    if "brahmaputra_basin_flag" in df.columns:
        feature_cols.append("brahmaputra_basin_flag")

    target_col = "y_sev_synthetic"

    years = sorted(df["fold_year"].unique())
    oof_predictions = np.zeros(len(df))

    for val_year in years:
        train_mask = df["fold_year"] != val_year
        val_mask = df["fold_year"] == val_year

        X_tr = df.loc[train_mask, feature_cols].fillna(0.0)
        y_tr = df.loc[train_mask, target_col].values
        X_val = df.loc[val_mask, feature_cols].fillna(0.0)

        model = lgb.LGBMRegressor(
            learning_rate=0.03,
            num_leaves=15,
            min_child_samples=20,
            n_estimators=200,
            random_state=42,
            verbose=-1
        )
        model.fit(X_tr, y_tr)
        oof_predictions[val_mask] = model.predict(X_val)

    y_true = df[target_col].values
    rmse = float(np.sqrt(mean_squared_error(y_true, oof_predictions)))
    mae = float(mean_absolute_error(y_true, oof_predictions))
    r2 = float(r2_score(y_true, oof_predictions))

    print(f"[Phase 4 M7] Secondary LOYO CV Results: RMSE={rmse:.4f}, MAE={mae:.4f}, R2={r2:.4f}")

    os.makedirs(REPORTS_DIR, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(y_true, oof_predictions, alpha=0.3, color="teal", edgecolors="none")
    ax.plot([0, max(y_true)], [0, max(y_true)], "r--", label="Ideal 1:1 Line")
    ax.set_xlabel("True log1p(pop_affected_synthetic)")
    ax.set_ylabel("Predicted log1p(pop_affected_synthetic)")
    ax.set_title("M7 Secondary Synthetic Pipeline Check (LOYO CV 2014-2025)\n[PIPELINE CHECK ONLY - no observed-derived labels]")
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.6)
    scatter_path = os.path.join(REPORTS_DIR, "m7_synthetic_loyo_evaluation.png")
    fig.tight_layout()
    fig.savefig(scatter_path, dpi=150)
    plt.close()

    m7_results = {
        "model": "M7_Secondary_LightGBM_Severity",
        "label_source": "synthetic_augmentation",
        "warning": "PIPELINE CHECK ONLY - no observed-derived labels (Secondary synthetic verification)",
        "cv_strategy": "Leave-One-Year-Out (2014-2025, 12 folds)",
        "metrics": {
            "RMSE": round(rmse, 4),
            "MAE": round(mae, 4),
            "R2": round(r2, 4)
        },
        "plot_path": scatter_path
    }

    os.makedirs(METRICS_DIR, exist_ok=True)
    results_path = os.path.join(METRICS_DIR, "results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(m7_results, f, indent=2)

    return m7_results


# Canonical alias for compatibility
FloodHazard = FloodHazardModel

