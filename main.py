"""
# Take-Home Exercise: Edge Sensor Processing & Cloud Sync

Role: Mid/Senior Python Software Engineer
Time budget: 3-4 hours (do not over-invest , see "What we're not grading" below)
Format: Submit a git repo (zip or link) with code, tests, and a short README

## Scenario

Our product monitors industrial equipment health using eg vibration sensors mounted directly on machines. Each sensor is read by a small edge device (think limited CPU, limited RAM, intermittent network). The edge device must process sensor data locally in near real time -> computing rolling health metrics and flagging anomalies, and periodically sync summarized data to AWS. The device cannot assume a reliable network connection at all times and cannot afford to lose data during outages.

You'll build a small but realistic slice of this pipeline: a synthetic physical sensor, an edge-side streaming processor, and a cloud sync layer.

## Constraints & non-functional requirements

- Pure Python + secure libs is fine; you may use additional libraries but you need justify anything non-obvious.
- The edge processing loop must run within a bounded, predictable storage footprint , call out in the README what that footprint is and how you'd verify it on constrained hardware.
- Code should be structured so Part 2 (edge) and Part 3 (cloud sync) are decoupled , e.g., the edge processor shouldn't block on S3 availability.

## Deliverables

1. Code (Parts 1-3) with tests covering at least: the anomaly detector against the known fault window, the ring buffer's bounded-storage behavior, and the durable-queue-survives-a-restart behavior.
2. `README.md` Open source grade covering:
   - How to run everything (generator → processor → sync) end to end.
   - Key design decisions and trade-offs, and what you'd change with more time.
   - A short (few paragraphs) section: "From prototype to production edge deployment" , how would this actually get deployed and operated on real edge hardware talking to AWS? Touch on things like: edge runtime/orchestration (e.g., AWS IoT Greengrass,, bare systemd), OTA updates, observability/alerting with constrained connectivity, and how you'd size the throughput/storage numbers for real hardware rather than a laptop.

## What we're not grading

- Production-grade AWS IAM/networking setup , mocked S3 is sufficient.
- Front-end/visualization , plain logs or a simple CLI summary are fine.
- Perfect anomaly detection accuracy , we care about a sound approach and honest evaluation of it, not a tuned model.
- Exhaustive test coverage , a handful of meaningful tests beats blanket coverage.

## Stretch goals (optional, only if time remains)

- Replace the threshold detector with a simple Kalman filter or EWMA-based detector and compare.
- Multi-sensor fusion (simulate 2-3 sensors, correlate anomalies across them).
- A one-page design sketch for the real AWS ingestion path at scale (connection/transformation/database) as an alternative to batched S3.
"""
import math

from services.edge_processing_service import EdgeProcessingService, compare_against_fault_window
from storage.s3_upload_process import S3UploadProcess
from services.vibration_sensor import vibration_sensor_simulator


def process_sensor(service:EdgeProcessingService, sensor, sample_rate, time=20, fault_time=None, fault_duration=None):
    frames = sample_rate * time

    for i in range(frames):
        frame_sensor_data = next(sensor)
        t, value = frame_sensor_data

        service.process(t, value)

    if fault_time is not None and fault_duration is not None:
        compare_against_fault_window(evaluated_t_list=service.evaluated_t_list, anomaly_t_list=service.anomaly_t_list, fault_time=fault_time,
                                     fault_duration=fault_duration)

    return service.anomaly_t_list


def main():
    # uploader = S3UploadProcess(
    #     db_path="data/windows.db",
    #     bucket="processed-windows",
    #     batch_size=100,
    #     interval=1.0,
    # )
    #
    # uploader.start()

    try:
        sample_rate = 1000
        sensor = vibration_sensor_simulator(sample_rate=sample_rate, fault_time=5.0, fault_duration=2.0, fault_omega_n=2 * math.pi * 70)
        service = EdgeProcessingService(sample_rate=sample_rate)

        anomaly_time_list = process_sensor(service, sensor, sample_rate, 20, fault_time=5.0, fault_duration=2.0)
        # print(anomaly_time_list)

    finally:
        # uploader.stop()
        pass




if __name__ == '__main__':
    main()
