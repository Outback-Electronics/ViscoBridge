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
    param_stderr: np.ndarray
    aic: float
    bic: float
    residuals: np.ndarray
    x: np.ndarray

    def __str__(self) -> str:
        parts = [
            f"{name} = {val:.4g} +/- {err:.4g}"
            for name, val, err in zip(self.param_names, self.params, self.param_stderr)
        ]
        return (
            f"{self.model_name}: " + ", ".join(parts)
            + f"  (R^2={self.r_squared:.4f}, AIC={self.aic:.2f}, BIC={self.bic:.2f})"
        )


def _aic_bic(n: int, k: int, ss_res: float) -> tuple[float, float]:
    # Gaussian-error AIC/BIC from residual sum of squares (standard form
    # for least-squares regression model comparison).
    if n <= 0 or ss_res <= 0:
        return float("nan"), float("nan")
    aic = n * np.log(ss_res / n) + 2 * k
    bic = n * np.log(ss_res / n) + k * np.log(n)
    return aic, bic


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
    residuals = tau - predicted
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((tau - np.mean(tau)) ** 2)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    stderr = np.sqrt(np.clip(np.diag(cov), 0, None))
    aic, bic = _aic_bic(len(gamma), len(params), ss_res)
    return FitResult(model_name, spec["params"], params, cov, r_squared, stderr, aic, bic, residuals, gamma)


def predict(model_name: str, params: np.ndarray, shear_rate: np.ndarray) -> np.ndarray:
    spec = MODELS[model_name]
    return spec["func"](np.asarray(shear_rate, dtype=float), *params)


# ---------------------------------------------------------------------------
# Temperature-dependence models (Arrhenius, WLF) for fitting viscosity vs.
# temperature data, e.g. from a Temperature Sweep test.
# ---------------------------------------------------------------------------

def _arrhenius(temp_c, a, ea_over_r):
    temp_k = np.asarray(temp_c, dtype=float) + 273.15
    return a * np.exp(ea_over_r / temp_k)


def _wlf(temp_c, mu_ref, c1, c2, t_ref_c=25.0):
    temp_c = np.asarray(temp_c, dtype=float)
    dt = temp_c - t_ref_c
    log_shift = -c1 * dt / (c2 + dt)
    return mu_ref * np.power(10.0, log_shift)


TEMP_MODELS = {
    "Arrhenius": {
        "func": _arrhenius,
        "params": ["A (pre-exponential)", "Ea/R (activation energy / gas const, K)"],
        "p0": lambda temp, visc: [np.min(visc), 2000.0],
        "bounds": (0, np.inf),
    },
    "WLF": {
        "func": _wlf,
        "params": ["mu_ref (viscosity @ Tref)", "C1", "C2 (K)"],
        "p0": lambda temp, visc: [np.mean(visc), 10.0, 100.0],
        "bounds": ([0, 0, 1e-3], [np.inf, 100, np.inf]),
    },
}


def fit_temperature_model(model_name: str, temp_c: np.ndarray, viscosity: np.ndarray) -> FitResult:
    if model_name not in TEMP_MODELS:
        raise ValueError(f"Unknown temperature model: {model_name}")
    spec = TEMP_MODELS[model_name]
    temp_c = np.asarray(temp_c, dtype=float)
    visc = np.asarray(viscosity, dtype=float)
    if len(temp_c) < len(spec["params"]) + 1:
        raise ValueError("Not enough data points to fit this model")

    p0 = spec["p0"](temp_c, visc)
    params, cov = curve_fit(spec["func"], temp_c, visc, p0=p0, bounds=spec["bounds"], maxfev=10000)
    predicted = spec["func"](temp_c, *params)
    residuals = visc - predicted
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((visc - np.mean(visc)) ** 2)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    stderr = np.sqrt(np.clip(np.diag(cov), 0, None))
    aic, bic = _aic_bic(len(temp_c), len(params), ss_res)
    return FitResult(model_name, spec["params"], params, cov, r_squared, stderr, aic, bic, residuals, temp_c)


def predict_temperature(model_name: str, params: np.ndarray, temp_c: np.ndarray) -> np.ndarray:
    spec = TEMP_MODELS[model_name]
    return spec["func"](np.asarray(temp_c, dtype=float), *params)


def confidence_ellipsoid(params: np.ndarray, covariance: np.ndarray, n_std: float = 2.0, resolution: int = 30):
    """For a 3-parameter fit, returns (x, y, z) mesh arrays tracing the
    n_std-sigma joint confidence ellipsoid implied by the fit's covariance
    matrix (eigendecomposition of cov scales a unit sphere by sqrt(eigenvalues)
    along the principal axes, same idea as a 2D confidence ellipse extended
    to 3D)."""
    if len(params) != 3:
        raise ValueError("Confidence ellipsoid requires exactly 3 fit parameters")

    eigvals, eigvecs = np.linalg.eigh(covariance)
    eigvals = np.clip(eigvals, 0, None)
    radii = n_std * np.sqrt(eigvals)

    u = np.linspace(0, 2 * np.pi, resolution)
    v = np.linspace(0, np.pi, resolution)
    sphere_x = np.outer(np.cos(u), np.sin(v))
    sphere_y = np.outer(np.sin(u), np.sin(v))
    sphere_z = np.outer(np.ones_like(u), np.cos(v))

    shape = sphere_x.shape
    points = np.stack([sphere_x.ravel(), sphere_y.ravel(), sphere_z.ravel()], axis=0) * radii[:, None]
    transformed = (eigvecs @ points) + np.asarray(params)[:, None]
    x, y, z = (transformed[i].reshape(shape) for i in range(3))
    return x, y, z
