import numpy as np
import pytest
from filter.kalman_filter import KalmanFilter2D, KalmanFilter3D

# ---------- KalmanFilter2D Tests ----------

def test_kalman2d_initialization():
    kf = KalmanFilter2D(0.0, 0.0, 1.0, dt=1.0, process_noise=0.01, measurement_noise=0.1)
    assert kf.get_value() == pytest.approx(0.0)
    assert kf.get_rate() == pytest.approx(0.0)


def test_kalman2d_predict_only():
    kf = KalmanFilter2D(0.0, 2.0, 1.0, dt=1.0, process_noise=0.0, measurement_noise=0.1)
    kf.predict()
    assert kf.get_value() == pytest.approx(2.0)  # 0 + 2 * 1
    assert kf.get_rate() == pytest.approx(2.0)


def test_kalman2d_update_changes_value():
    kf = KalmanFilter2D(0.0, 0.0, 1.0, dt=1.0, process_noise=0.01, measurement_noise=0.1)
    kf.predict()
    pre_value = kf.get_value()
    kf.update(10.0)
    post_value = kf.get_value()
    assert not np.isclose(pre_value, post_value)


# ---------- KalmanFilter3D Tests ----------

def test_kalman3d_initialization():
    kf = KalmanFilter3D(0.0, 0.0, 0.0, initial_variance=1.0, dt=1.0,
                        process_noise=0.01, measurement_noise=0.1)
    assert kf.get_value() == pytest.approx(0.0)
    assert kf.get_rate() == pytest.approx(0.0)
    assert kf.get_acceleration() == pytest.approx(0.0)


def test_kalman3d_predict_only():
    kf = KalmanFilter3D(0.0, 1.0, 2.0, initial_variance=1.0, dt=1.0,
                        process_noise=0.0, measurement_noise=0.1)
    kf.predict()
    expected_value = 0 + 1*1 + 0.5*2*1**2  # = 2.0
    expected_rate = 1 + 2*1               # = 3.0
    expected_acc = 2.0
    assert kf.get_value() == pytest.approx(expected_value)
    assert kf.get_rate() == pytest.approx(expected_rate)
    assert kf.get_acceleration() == pytest.approx(expected_acc)


def test_kalman3d_update_changes_value():
    kf = KalmanFilter3D(0.0, 0.0, 0.0, initial_variance=1.0, dt=1.0,
                        process_noise=0.01, measurement_noise=0.1)
    kf.predict()
    pre_value = kf.get_value()
    kf.update(5.0)
    post_value = kf.get_value()
    assert not np.isclose(pre_value, post_value)
