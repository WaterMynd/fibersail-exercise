import math
import time

from services.edge_processing_service import EdgeProcessingService
from services.vibration_sensor import vibration_sensor_simulator


def benchmark():
    sample_rate = 1000
    sensor = vibration_sensor_simulator(sample_rate=sample_rate, fault_time=5.0, fault_duration=2.0, fault_omega_n=2 * math.pi * 70)
    service = EdgeProcessingService(sensor=sensor, sample_rate=sample_rate)

    start = time.time()
    evaluated_t_list, anomaly_time_list = service.process(20)
    elapsed_time = time.time() - start
    print(f"Throughput = {len(evaluated_t_list) / elapsed_time} samples/sec")


if __name__ == '__main__':
    benchmark()
