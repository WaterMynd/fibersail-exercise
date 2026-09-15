import multiprocessing

from storage.local_queue import LocalPersistentQueue
from storage.s3_uploader import S3Uploader


class S3UploadProcess:
    INITIAL_BACKOFF = 1.0
    MAX_BACKOFF = 60.0

    def __init__(self, db_path: str, bucket: str, batch_size: int = 100, interval: float = 1.0):
        self.db_path = db_path
        self.bucket = bucket
        self.batch_size = batch_size
        self.interval = interval

        self._stop_event = multiprocessing.Event()

        self._process = multiprocessing.Process(
            target=self._run,
            name="s3-upload-process",
        )

    def start(self):
        self._process.start()

    def stop(self):
        self._stop_event.set()
        self._process.join()

    def _run(self):
        local_queue = LocalPersistentQueue(self.db_path)

        uploader = S3Uploader(
            bucket=self.bucket,
        )

        backoff = self.INITIAL_BACKOFF

        while not self._stop_event.is_set():
            windows = local_queue.get_pending_windows(
                limit=self.batch_size
            )

            if not windows:
                self._stop_event.wait(self.interval)
                continue

            # TODO - Missing having a minimum batch number to upload to prevent uploading 1 by 1

            ids = [window["id"] for window in windows]

            try:
                batch_id = f"{ids[0]}-{ids[-1]}"

                uploader.upload_batch(
                    batch_id=batch_id,
                    windows=windows,
                )

                # Only delete after successful upload.
                local_queue.delete_windows(ids)

                print(
                    f"[S3] Uploaded {len(windows)} windows"
                )

                # Connectivity has returned.
                # Reset the backoff.
                backoff = self.INITIAL_BACKOFF

            except Exception as exc:
                print(
                    f"[S3] Upload failed: {exc}. "
                    f"Retrying in {backoff:.1f}s"
                )

                self._stop_event.wait(backoff)

                backoff = min(
                    backoff * 2,
                    self.MAX_BACKOFF,
                )
