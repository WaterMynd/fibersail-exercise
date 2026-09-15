import pytest

from services.edge_processing_service import compare_against_fault_window


def test_all_predictions_inside_fault_window():
    evaluated_t = [1, 2, 3, 4, 5]
    anomaly_t = [2, 3, 4]

    result = compare_against_fault_window(
        evaluated_t,
        anomaly_t,
        fault_time=2,
        fault_duration=3,
    )

    tp, fp, fn, tn, precision, recall = result

    assert tp == 3
    assert fp == 0
    assert fn == 0
    assert tn == 2
    assert precision == pytest.approx(1.0)
    assert recall == pytest.approx(1.0)


def test_false_positives_outside_fault_window():
    evaluated_t = [1, 2, 3, 4, 5]
    anomaly_t = [1, 5]

    result = compare_against_fault_window(
        evaluated_t,
        anomaly_t,
        fault_time=2,
        fault_duration=3,
    )

    tp, fp, fn, tn, precision, recall = result

    assert tp == 0
    assert fp == 2
    assert fn == 3
    assert tn == 0
    assert precision == pytest.approx(0.0)
    assert recall == pytest.approx(0.0)


def test_false_negatives_inside_fault_window():
    evaluated_t = [1, 2, 3, 4, 5]
    anomaly_t = [2]

    result = compare_against_fault_window(
        evaluated_t,
        anomaly_t,
        fault_time=2,
        fault_duration=3,
    )

    tp, fp, fn, tn, precision, recall = result

    assert tp == 1
    assert fp == 0
    assert fn == 2
    assert tn == 2
    assert precision == pytest.approx(1.0)
    assert recall == pytest.approx(1 / 3)


def test_mixed_predictions():
    evaluated_t = [1, 2, 3, 4, 5, 6]
    anomaly_t = [1, 2, 4, 6]

    result = compare_against_fault_window(
        evaluated_t,
        anomaly_t,
        fault_time=2,
        fault_duration=3,
    )

    tp, fp, fn, tn, precision, recall = result

    assert tp == 2
    assert fp == 2
    assert fn == 1
    assert tn == 1
    assert precision == pytest.approx(0.5)
    assert recall == pytest.approx(2 / 3)


def test_fault_window_end_is_exclusive():
    evaluated_t = [10, 11, 12, 13]
    anomaly_t = [10, 12, 13]

    result = compare_against_fault_window(
        evaluated_t,
        anomaly_t,
        fault_time=10,
        fault_duration=3,
    )

    tp, fp, fn, tn, precision, recall = result

    assert tp == 2
    assert fp == 1
    assert fn == 1
    assert tn == 0
    assert precision == pytest.approx(2 / 3)
    assert recall == pytest.approx(2 / 3)


def test_no_anomalies():
    evaluated_t = [1, 2, 3, 4, 5]

    result = compare_against_fault_window(
        evaluated_t,
        anomaly_t_list=[],
        fault_time=2,
        fault_duration=2,
    )

    tp, fp, fn, tn, precision, recall = result

    assert tp == 0
    assert fp == 0
    assert fn == 2
    assert tn == 3
    assert precision == pytest.approx(0.0)
    assert recall == pytest.approx(0.0)


def test_no_evaluated_times():
    result = compare_against_fault_window(
        evaluated_t_list=[],
        anomaly_t_list=[1, 2, 3],
        fault_time=2,
        fault_duration=2,
    )

    tp, fp, fn, tn, precision, recall = result

    assert tp == 0
    assert fp == 0
    assert fn == 0
    assert tn == 0
    assert precision == pytest.approx(0.0)
    assert recall == pytest.approx(0.0)


def test_anomalies_not_in_evaluated_times_are_ignored():
    evaluated_t = [1, 2, 3]
    anomaly_t = [2, 3, 100]

    result = compare_against_fault_window(
        evaluated_t,
        anomaly_t,
        fault_time=2,
        fault_duration=2,
    )

    tp, fp, fn, tn, precision, recall = result

    # 100 is not in evaluated_t, so it cannot contribute to FP.
    assert tp == 2
    assert fp == 0
    assert fn == 0
    assert tn == 1
    assert precision == pytest.approx(1.0)
    assert recall == pytest.approx(1.0)


def test_duplicate_anomaly_times_do_not_change_result():
    evaluated_t = [1, 2, 3, 4]
    anomaly_t = [2, 2, 2, 3]

    result = compare_against_fault_window(
        evaluated_t,
        anomaly_t,
        fault_time=2,
        fault_duration=2,
    )

    tp, fp, fn, tn, precision, recall = result

    assert tp == 2
    assert fp == 0
    assert fn == 0
    assert tn == 2
    assert precision == pytest.approx(1.0)
    assert recall == pytest.approx(1.0)

