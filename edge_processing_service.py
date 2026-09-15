"""
## Part 2 , Edge processing service

Build a streaming processor that consumes the sensor stream in real time (or at simulated real-time speed) and:

- Maintains a bounded rolling window (e.g., 1-2 seconds) using an efficient structure, storage must not grow unbounded as the stream runs.
- Computes rolling features per window: RMS, rolling mean/std, and dominant frequency (FFT peak). No look-ahead , only use data available up to the current point.
- Flags anomalies and reports precision/recall-style stats against the known fault-injection window from Part 1.
- Sustains at least 1000 samples/sec of throughput on a single core on typical laptop hardware, without falling behind. Include a way to demonstrate this (a benchmark script or test with timing output).
"""

from collections import deque

import numpy as np

from storage.local_queue import LocalPersistentQueue


class EdgeProcessingService:
    def __init__(self, sample_rate=1000, window_seconds=2, expected_frequency=50.0):
        self.sample_rate = sample_rate
        self.window_size = int(
            sample_rate * window_seconds)  # Larger windows give more stable FFT estimates but increase detection latency because the first features are only calculated when we have 2 seconds of data
        self.expected_frequency = expected_frequency

        self.sample_window = deque(maxlen=self.window_size)
        self.evaluated_t_list = []
        self.anomaly_t_list = []

        self.local_queue = LocalPersistentQueue()

    def calculate_features(self, samples, sample_rate):
        """
        Root Mean Square - Measures the overall magnitude or energy of a signal.
        Rolling Mean - It smooths the signal and shows its local/short-term average level. For sensor data, it can help distinguish a gradual change in the baseline from rapid fluctuations.
        Rolling Standard Deviation - Tells how variable/noisy the signal is right now
        Dominant frequency (FFTpeak) - Tells what frequency is the strongest/most prominent in this signal
        """

        values = np.asarray(samples, dtype=float)

        mean = np.mean(values)
        std = np.std(values)
        rms = np.sqrt(np.mean(values ** 2))

        centered = values - mean
        spectrum = np.abs(np.fft.rfft(centered))

        # Ignore DC component at index 0.
        spectrum[0] = 0

        peak_index = np.argmax(spectrum)

        frequencies = np.fft.rfftfreq(len(values), d=1.0 / sample_rate)

        dominant_frequency = frequencies[peak_index]

        return {
            "mean": mean,
            "std": std,
            "rms": rms,
            "dominant_frequency": dominant_frequency
        }

    def is_anomaly(self, features, expected_frequency):
        # The exact thresholds should be calibrated against your generated baseline data rather than treated as universal vibration limits.
        frequency_changed = (
                abs(features["dominant_frequency"] - expected_frequency) > 10.0
        )

        unusually_high_rms = features["rms"] > 2.0

        return frequency_changed or unusually_high_rms

    def process(self, time, value):
        self.sample_window.append(value)

        if len(self.sample_window) == self.window_size:
            self.evaluated_t_list.append(time)
            features = self.calculate_features(samples=self.sample_window, sample_rate=self.sample_rate)

            is_anomaly = self.is_anomaly(features, expected_frequency=50)
            if is_anomaly:
                self.anomaly_t_list.append(time)

            # self.local_queue.save_window(
            #     timestamp=time,
            #     samples=list(self.sample_window),
            #     features=features,
            #     anomaly=is_anomaly
            # )


def compare_against_fault_window(evaluated_t_list, anomaly_t_list, fault_time, fault_duration):
    fault_end = fault_time + fault_duration

    anomaly_times = set(anomaly_t_list)

    true_positive = 0
    false_positive = 0
    false_negative = 0
    true_negative = 0

    for t in evaluated_t_list:
        actual_fault = fault_time <= t < fault_end
        predicted_anomaly = t in anomaly_times

        if actual_fault and predicted_anomaly:
            true_positive += 1
        elif not actual_fault and predicted_anomaly:
            false_positive += 1
        elif actual_fault and not predicted_anomaly:
            false_negative += 1
        else:
            true_negative += 1

    precision = (
        true_positive / (true_positive + false_positive)
        if true_positive + false_positive
        else 0.0
    )

    recall = (
        true_positive / (true_positive + false_negative)
        if true_positive + false_negative
        else 0.0
    )

    print(f"TP: {true_positive}")
    print(f"FP: {false_positive}")
    print(f"FN: {false_negative}")
    print(f"TN: {true_negative}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall: {recall:.3f}")
    return true_positive, false_positive, false_negative, true_negative, precision, recall
