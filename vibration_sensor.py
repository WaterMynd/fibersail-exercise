"""
## Part 1 , Simulated sensor (physics)

Implement a synthetic vibration sensor as a damped harmonic oscillator driven by noise, sampled at a configurable rate (default 1 kHz):

```
x''(t) + 2*zeta*omega_n*x'(t) + omega_n^2*x(t) = F(t)
```

Requirements:

- Numerically integrate the system (e.g., RK4 or `scipy.integrate`) to produce a displacement or acceleration time series.
- `F(t)` should be mostly Gaussian noise, representing normal operating vibration.
- Add a mechanism to inject a fault: at a chosen time, shift `omega_n` and/or `zeta` (simulating bearing wear or a loosening mount) for a configurable duration, then return to baseline.
- The generator should emit samples as a stream (an iterator/generator or callback), not a precomputed array , the edge service should not assume it has the whole array up front.

You don't need to be a controls engineer , the point is a plausible synthetic time series with a known ground-truth anomaly window, so we can check whether your detector actually finds it. **If you are blocked here, use the sample_dataset_small.csv as base dataset**, state your simplifying assumptions in the README.

"""
import math
import random


def vibration_sensor_simulator(sample_rate=1000.0, omega_n=2 * math.pi * 50, zeta=0.05, noise_std=1.0,
                               fault_time=None, fault_duration=0.0, fault_omega_n=None, fault_zeta=None):
    """
    Generate a synthetic vibration sensor stream.

    Yields:
        (time, displacement, acceleration)
    """
    t = 0.0  # time
    displacement = 0.0
    velocity = 0.0

    dt = 1.0 / sample_rate

    def acceleration(x, v, omega, damping, force):
        return force - 2.0 * damping * omega * v - omega ** 2 * x

    while True:
        # Decide whether the fault is active
        fault_active = (fault_time is not None and fault_time <= t < fault_time + fault_duration)

        if fault_active:
            current_omega = fault_omega_n if fault_omega_n is not None else omega_n
            current_zeta = fault_zeta if fault_zeta is not None else zeta
        else:
            current_omega = omega_n
            current_zeta = zeta

        # Gaussian noise = external force F(t)
        force = random.gauss(0.0, noise_std)

        # RK4 integration
        k1_x = velocity
        k1_v = acceleration(displacement, velocity, current_omega, current_zeta, force)

        k2_x = velocity + 0.5 * dt * k1_v
        k2_v = acceleration(displacement + 0.5 * dt * k1_x, velocity + 0.5 * dt * k1_v, current_omega, current_zeta, force)

        k3_x = velocity + 0.5 * dt * k2_v
        k3_v = acceleration(displacement + 0.5 * dt * k2_x, velocity + 0.5 * dt * k2_v, current_omega, current_zeta, force)

        k4_x = velocity + dt * k3_v
        k4_v = acceleration(            displacement + dt * k3_x,            velocity + dt * k3_v,            current_omega,            current_zeta,force)

        # Update state
        displacement += dt / 6.0 * (k1_x + 2 * k2_x + 2 * k3_x + k4_x)
        velocity += dt / 6.0 * (k1_v + 2 * k2_v + 2 * k3_v + k4_v)

        t += dt

        # Output acceleration corresponding to the current state
        a = acceleration(
            displacement, velocity, current_omega, current_zeta, force
        )

        yield t, a
