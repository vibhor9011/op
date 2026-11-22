"""Base Hazard Model Interface for OrbitGuard Multi-Hazard Early Warning."""

from abc import ABC, abstractmethod
from typing import Any, Optional
import numpy as np
import pandas as pd


class BaseHazardModel(ABC):
    """
    Abstract interface that all hazard modules (flood, landslide, heat, etc.) must implement.
    Methods:
        build_features(df)
        build_labels(df)
        fit(X_train, y_train_cls, y_train_reg)
        predict(X) -> DataFrame[p_low, p_mid, p_high]
        extent(period) -> dict or None
        explain(X) -> dict
    """

    def __init__(self, hazard_name: str = "flood"):
        self.hazard_name = hazard_name
        self.is_fitted = False

    @abstractmethod
    def build_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract and prepare model input features from raw/ingested tables."""
        pass

    @abstractmethod
    def build_labels(self, df: pd.DataFrame) -> tuple:
        """Extract classification (T_cls) and regression (T_reg) target labels."""
        pass

    @abstractmethod
    def fit(self, X_train: pd.DataFrame, y_train_cls: pd.Series, y_train_reg: pd.Series = None):
        """Fit the hazard model on training features and targets."""
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """Predict hazard probabilities returning DataFrame with columns [p_low, p_mid, p_high]."""
        pass

    @abstractmethod
    def extent(self, period: Optional[str] = None) -> Any:
        """Spatial extent configuration and footprint generation."""
        pass

    @abstractmethod
    def explain(self, X: pd.DataFrame) -> dict:
        """Return global feature importances and local explanations."""
        pass
