import numpy as np
import pytest
from filter.KalmanFilter import KalmanFilter2D, KalmanFilter3D


def test_kf2d_initialization():
    kf = KalmanFilter2D(initial_value=10.0, initial_rate=1.0)
    assert kf.get_type() == "2D"
    assert np.isclose(kf.get_value(), 10.0)
    assert np.isclose(kf.get_rate(), 1.0)
    assert kf.P.shape == (2, 2)


def test_kf2d_predict_moves_state():
    kf = KalmanFilter2D(initial_value=0.0, initial_rate=1.0, dt=1.0)
    kf.predict()
    # After one second with rate 1.0, value should be ~1.0
    assert np.isclose(kf.get_value(), 1.0, atol=1e-8)
    assert np.isclose(kf.get_rate(), 1.0, atol=1e-8)


def test_kf2d_update_moves_toward_measurement():
    kf = KalmanFilter2D(initial_value=0.0, initial_rate=0.0)
    kf.update(5.0)
    # Value should move closer to 5
    assert 0.0 < kf.get_value() < 5.0


def test_kf3d_initialization():
    kf = KalmanFilter3D(initial_value=2.0, initial_rate=0.5, initial_acceleration=0.1)
    assert kf.get_type() == "3D"
    assert np.isclose(kf.get_value(), 2.0)
    assert np.isclose(kf.get_rate(), 0.5)
    assert np.isclose(kf.get_acceleration(), 0.1)
    assert kf.P.shape == (3, 3)


def test_kf3d_predict_moves_state_with_accel():
    kf = KalmanFilter3D(initial_value=0.0, initial_rate=1.0, initial_acceleration=1.0, dt=1.0)
    kf.predict()
    # New value = old value + rate*dt + 0.5*accel*dt^2 = 0 + 1*1 + 0.5*1*1 = 1.5
    assert np.isclose(kf.get_value(), 1.5, atol=1e-8)
    # New rate = old rate + accel*dt = 1 + 1 = 2
    assert np.isclose(kf.get_rate(), 2.0, atol=1e-8)
