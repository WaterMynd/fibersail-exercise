import numpy as np


def calculate_rms(samples):
    """Root Mean Square of a window of samples."""
    return np.sqrt(np.mean(samples ** 2))


def calculate_rolling_mean(samples):
    """Mean and standard deviation of a window of samples."""
    return np.mean(samples)


def calculate_rolling_standard_deviation(samples):
    """Mean and standard deviation of a window of samples."""
    return np.std(samples)


def calculate_dominant_frequency(samples, sample_rate):
    """Return the dominant frequency in Hz using the FFT peak."""
    # Remove DC component so a non-zero average doesn't dominate the FFT.
    samples = samples - np.mean(samples)

    spectrum = np.fft.rfft(samples)
    magnitudes = np.abs(spectrum)

    # Ignore the 0 Hz bin.
    peak_index = np.argmax(magnitudes[1:]) + 1

    frequencies = np.fft.rfftfreq(
        len(samples),
        d=1.0 / sample_rate,
    )

    return frequencies[peak_index]