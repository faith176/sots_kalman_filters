import numpy as np

class KalmanFilter2D:
    def __init__(self,
                 initial_value=0.0,
                 initial_rate=0.0,
                 initial_variance=1.0,
                 dt=1.0,
                 process_noise=0.01,
                 measurement_noise=0.1):
        self.state = np.array([[initial_value], [initial_rate]])  # State vector: [value, rate]
        self.P = np.array([[initial_variance, 0], [0, initial_variance]])  # Covariance

        self.dt = dt
        self.Q = np.array([[process_noise, 0], [0, process_noise]])  # Process noise
        self.R = measurement_noise  # Measurement noise (scalar, since we only update using one value)
        self.H = np.array([[1, 0]])  # Measurement matrix
        self.I = np.eye(2) # Identity matrix

        # State transition matrix
        self.F = np.array([
                [1, self.dt],
                [0, 1]
            ])


    def predict(self):
        # Predict state
        self.state = self.F @ self.state
        # Predict covariance
        self.P = self.F @ self.P @ self.F.T + self.Q


    def update(self, measurement):
        # Innovation
        y = np.array([[measurement]]) - self.H @ self.state

        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R

        # Kalman gain
        K = self.P @ self.H.T / S

        # Update state
        self.state += K @ y

        # Update covariance
        self.P = (self.I - K @ self.H) @ self.P

    def get_type(self):
        return "2D"
    
    def get_value(self):
        return self.state[0, 0]

    def get_rate(self):
        return self.state[1, 0]

    def get_covariance(self):
        return self.P



class KalmanFilter3D:
    def __init__(self,
                 initial_value=0.0,
                 initial_rate=0.0,
                 initial_acceleration=0.0,
                 initial_variance=1.0,
                 dt=1.0,
                 process_noise=0.01,
                 measurement_noise=0.1):
        self.dt = dt
        dt2 = 0.5 * dt ** 2

        # State vector: [value, rate, acceleration]
        self.state = np.array([[initial_value],
                               [initial_rate],
                               [initial_acceleration]])
        self.P = np.eye(3) * initial_variance  # Covariance matrix
        self.Q = np.eye(3) * process_noise # Process noise
        self.H = np.array([[1, 0, 0]]) # Measurement matrix
        self.R = measurement_noise # Measurement noise (scalar, since we only update using one value)        
        self.I = np.eye(3) # Identity matrix

        # State transition matrix
        self.F = np.array([
            [1, dt, dt2],
            [0, 1, dt],
            [0, 0, 1]
        ])

    def predict(self):
        # Predict state
        self.state = self.F @ self.state

        # Predict covariance
        self.P = self.F @ self.P @ self.F.T + self.Q

    def update(self, measurement):
        # Innovation
        y = np.array([[measurement]]) - self.H @ self.state

        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R

        # Kalman gain
        K = self.P @ self.H.T / S 

        # Update state
        self.state += K @ y

        # Update covariance
        self.P = (self.I - K @ self.H) @ self.P

    def get_type(self):
        return "3D"

    def get_value(self):
        return self.state[0, 0]

    def get_rate(self):
        return self.state[1, 0]

    def get_acceleration(self):
        return self.state[2, 0]

    def get_covariance(self):
        return self.P

