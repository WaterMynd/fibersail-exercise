# Take-Home Exercise: Edge Sensor Processing & Cloud Sync


## Constraints & non-functional requirements

### Additional libraries
NumPy — Used for numerical processing of the vibration signal, including RMS/mean/std calculations and FFT-based dominant frequency detection. It provides significantly more efficient array and FFT operations than implementing these calculations manually in Python.
boto3 — Used to communicate with Amazon S3 from the cloud synchronization component. It provides the AWS SDK functionality needed to upload processed sensor data and is preferable to implementing S3 HTTP requests manually.

### The edge processing loop must run within a bounded, predictable memory footprint , call out in the README what that footprint is and how you'd verify it on constrained hardware.
The edge processor uses a fixed-size collections.deque with a fixed size of 2000 samples. The deque, once 2,000 samples are stored, each new sample automatically removes the oldest sample making the memory used is stable and limited.

### Code should be structured so Part 2 (edge) and Part 3 (cloud sync) are decoupled , e.g., the edge processor shouldn't block on S3 availability.
The edge processor sends its processed outputs to a local persistent queue, which is then read by a separate process responsible for uploading the data to S3.
This means that the edge processor does not need to know about S3 or wait for its availability. Similarly, the cloud synchronization process only interacts with the local queue and S3, keeping the two components independent. This ensures that temporary network or S3 outages do not block the edge processing pipeline.

### Tests
Anomaly detector against the known fault window: tested
Ring buffer's bounded-memory behavior: tested, since it's a deque it should behave as expected
The durable-queue-survives-a-restart behavior: didn't have time to implement this test, theoretically this was taken into account, we have a local persistent db that stores the outputs in a queue, and a separate process processes it.


### How to run everything (generator → processor → sync) end to end.
Running main.py starts the edge processor, which processes data from the sensor generator for 20 seconds. At the end, it prints the precision and recall results for the anomaly detector.
The code for saving the edge processor outputs to a local persistent database has been implemented but not fully tested. The database helps prevent data loss if the process is restarted. However, data could still be lost if the device shuts down while data is being written to the database.
The cloud sync process checks the local database and uploads the stored outputs to S3. The S3 uploader service has also been implemented. One remaining TODO is to upload the data in batches instead of individually. The uploader should wait until a certain number of outputs are available before uploading them. If the network is unavailable, it should also use a backoff strategy to avoid repeatedly trying to connect and overloading the network.

The benchmark is available in benchmark_test.py.


### Key design decisions and trade-offs, and what you'd change with more time.
A deque with a fixed size was used for the rolling buffer so that memory usage stays bounded. The trade-off is that older samples are discarded once the buffer is full.
A local persistent database was used to decouple the edge processor from the cloud uploader. This means the edge can continue processing when the network or S3 is unavailable. The trade-off is that the database uses disk space, and the uploader needs to process the stored data later.
The anomaly detector uses simple statistical features and frequency analysis instead of a more complex machine learning model. This keeps the solution lightweight and suitable for a constrained edge device, but it may not detect more complex faults.
With more time, I would finish and improve the S3 upload process, implement a more complex model to detect anomalies, add tests regarding the database persistence and S3 failures.


### A short (few paragraphs) section: "From prototype to production edge deployment" , how would this actually get deployed and operated on real edge hardware talking to AWS? Touch on things like: edge runtime/orchestration (e.g., AWS IoT Greengrass,, bare systemd), OTA updates, observability/alerting with constrained connectivity, and how you'd size the throughput/memory numbers for real hardware rather than a laptop.
In production, the edge processor and the S3 uploader would run as separate services on the device. They could be managed with systemd or AWS IoT Greengrass. The device would securely connect to AWS, and the local queue would keep data safe when the network is unavailable.
Updates could be sent remotely to the edge device. The application should be versioned so that new versions can be installed and, if necessary, rolled back. This could be done with a periodic check of the version somewhere in the cloud.
The device should also keep simple logs and metrics such as processing errors, queue size, and upload failures. Alerts can be sent to a support channel (email or slack or even AWS service for support) when the connection is available (similar to the process output queue).
Before deployment, the system should be tested on the actual hardware. We would measure CPU, memory, and processing speed to make sure it can handle the sensor rate (for example, 1,000 samples/second) with some extra capacity.

### S3 bucket structure proposal assuming there's a S3 bucket per client
s3://<bucket>/
└── machine_model/
    └── <machine_id>/
        └── date=YYYY-MM-DD/
            └── hour=HH/
                └── <timestamp>.json

The machine model and id are first partitions so data from different machines can be isolated easily. Data is then partitioned by date and hour, which keeps individual prefixes manageable and makes time-range queries straightforward.
Each object contains the raw sensor samples along with their timestamps and relevant metadata. Storing the raw samples in S3 allows the data to be reprocessed later for more detailed analysis, debugging, or the development of improved anomaly detection methods.
