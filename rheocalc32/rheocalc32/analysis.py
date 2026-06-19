from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import curve_fit


def _newtonian(gamma, mu):
    return mu * gamma


def _power_law(gamma, k, n):
    return k * np.power(gamma, n)


def _bingham(gamma, tau0, mu):
    return tau0 + mu * gamma


def _herschel_bulkley(gamma, tau0, k, n):
    return tau0 + k * np.power(gamma, n)


def _casson(gamma, tau0, mu):
    return (np.sqrt(np.maximum(tau0, 0)) + np.sqrt(np.maximum(mu, 0)) * np.sqrt(gamma)) ** 2


MODELS = {
    "Newtonian": {
        "func": _newtonian,
        "params": ["viscosity (Pa.s equiv.)"],
        "p0": lambda gamma, tau: [np.mean(tau) / max(np.mean(gamma), 1e-9)],
        "bounds": (0, np.inf),
    },
    "Power Law": {
        "func": _power_law,
        "params": ["K (consistency index)", "n (flow index)"],
        "p0": lambda gamma, tau: [1.0, 1.0],
        "bounds": (0, np.inf),
    },
    "Bingham": {
        "func": _bingham,
        "params": ["tau0 (yield stress)", "viscosity"],
        "p0": lambda gamma, tau: [max(np.min(tau), 0.0), 1.0],
        "bounds": (0, np.inf),
    },
    "Herschel-Bulkley": {
        "func": _herschel_bulkley,
        "params": ["tau0 (yield stress)", "K (consistency index)", "n (flow index)"],
        "p0": lambda gamma, tau: [max(np.min(tau), 0.0), 1.0, 1.0],
        "bounds": (0, np.inf),
    },
    "Casson": {
        "func": _casson,
        "params": ["tau0 (yield stress)", "viscosity"],
        "p0": lambda gamma, tau: [max(np.min(tau), 0.0), 1.0],
        "bounds": (0, np.inf),
    },
}


@dataclass
class FitResult:
    model_name: str
    param_names: list[str]
    params: np.ndarray
    covariance: np.ndarray
    r_squared: float

    def __str__(self) -> str:
        parts = [f"{name} = {val:.4g}" for name, val in zip(self.param_names, self.params)]
        return f"{self.model_name}: " + ", ".join(parts) + f"  (R^2={self.r_squared:.4f})"


def fit_model(model_name: str, shear_rate: np.ndarray, shear_stress: np.ndarray) -> FitResult:
    if model_name not in MODELS:
        raise ValueError(f"Unknown model: {model_name}")
    spec = MODELS[model_name]
    gamma = np.asarray(shear_rate, dtype=float)
    tau = np.asarray(shear_stress, dtype=float)
    mask = gamma > 0
    gamma, tau = gamma[mask], tau[mask]
    if len(gamma) < len(spec["params"]) + 1:
        raise ValueError("Not enough data points to fit this model")

    p0 = spec["p0"](gamma, tau)
    params, cov = curve_fit(spec["func"], gamma, tau, p0=p0, bounds=spec["bounds"], maxfev=10000)
    predicted = spec["func"](gamma, *params)
    ss_res = np.sum((tau - predicted) ** 2)
    ss_tot = np.sum((tau - np.mean(tau)) ** 2)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return FitResult(model_name, spec["params"], params, cov, r_squared)


def predict(model_name: str, params: np.ndarray, shear_rate: np.ndarray) -> np.ndarray:
    spec = MODELS[model_name]
    return spec["func"](np.asarray(shear_rate, dtype=float), *params)
