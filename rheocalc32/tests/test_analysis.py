import numpy as np

from rheocalc32 import analysis


def test_power_law_fit_recovers_parameters():
    gamma = np.linspace(1, 200, 50)
    k_true, n_true = 2.5, 0.7
    tau = k_true * gamma**n_true
    result = analysis.fit_model("Power Law", gamma, tau)
    k_fit, n_fit = result.params
    assert abs(k_fit - k_true) < 0.05
    assert abs(n_fit - n_true) < 0.02
    assert result.r_squared > 0.999


def test_newtonian_fit():
    gamma = np.linspace(1, 100, 30)
    mu_true = 15.0
    tau = mu_true * gamma
    result = analysis.fit_model("Newtonian", gamma, tau)
    assert abs(result.params[0] - mu_true) < 0.05


def test_bingham_fit():
    gamma = np.linspace(1, 100, 30)
    tau0_true, mu_true = 5.0, 3.0
    tau = tau0_true + mu_true * gamma
    result = analysis.fit_model("Bingham", gamma, tau)
    assert abs(result.params[0] - tau0_true) < 0.1
    assert abs(result.params[1] - mu_true) < 0.05
