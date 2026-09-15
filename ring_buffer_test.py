from collections import deque

import pytest

from services.edge_processing_service import EdgeProcessingService


@pytest.fixture
def service():
    return EdgeProcessingService(
        sensor=None,
        sample_rate=1000,
        window_seconds=2,
    )


def test_sample_window_is_a_deque(service):
    assert isinstance(service.sample_window, deque)


def test_sample_window_maxlen_is_window_size(service):
    assert service.sample_window.maxlen == 2000
    assert service.window_size == 2000


def test_sample_window_does_not_exceed_window_size(service):
    for i in range(5000):
        service.sample_window.append(i)

    assert len(service.sample_window) == service.window_size
    assert len(service.sample_window) <= service.window_size


def test_oldest_samples_are_evicted_when_window_is_full(service):
    for i in range(service.window_size):
        service.sample_window.append(i)

    assert service.sample_window[0] == 0
    assert service.sample_window[-1] == service.window_size - 1

    # Add one new sample.
    service.sample_window.append(service.window_size)

    assert len(service.sample_window) == service.window_size
    assert service.sample_window[0] == 1
    assert service.sample_window[-1] == service.window_size


def test_sample_window_contains_only_most_recent_samples(service):
    for i in range(service.window_size + 100):
        service.sample_window.append(i)

    expected = range(100, service.window_size + 100)

    assert list(service.sample_window) == list(expected)


def test_sample_window_remains_bounded_over_long_sequence(service):
    for i in range(100_000):
        service.sample_window.append(i)

        # Core bounded-storage invariant.
        assert len(service.sample_window) <= service.window_size

    assert len(service.sample_window) == service.window_size
    assert service.sample_window[0] == 100_000 - service.window_size
    assert service.sample_window[-1] == 99_999


@pytest.mark.parametrize(
    "sample_rate,window_seconds,expected_size",
    [
        (100, 1, 100),
        (1000, 2, 2000),
        (2000, 0.5, 1000),
        (5000, 10, 50_000),
    ],
)
def test_window_size_is_derived_from_sample_rate_and_duration(
    sample_rate,
    window_seconds,
    expected_size,
):
    service = EdgeProcessingService(
        sensor=None,
        sample_rate=sample_rate,
        window_seconds=window_seconds,
    )

    assert service.window_size == expected_size
    assert service.sample_window.maxlen == expected_size


def test_window_is_exactly_full_at_window_size(service):
    for i in range(service.window_size):
        service.sample_window.append(i)

    assert len(service.sample_window) == service.window_size


def test_adding_samples_after_full_does_not_grow_buffer(service):
    for i in range(service.window_size):
        service.sample_window.append(i)

    original_length = len(service.sample_window)

    for i in range(1000):
        service.sample_window.append(service.window_size + i)

    assert len(service.sample_window) == original_length

