import csv
import os
import time
import psutil
import threading


class Profiler:
    """Logs FPS, CPU%, RAM, and vision timing to a CSV."""

    FIELDS = [
        "timestamp",
        "elapsed_s",
        "fps",
        "cpu_pct",
        "ram_pct",
        "ram_mb",
        "detect_ms",
        "gesture_ms",
        "faces",
        "hands",
        "capture_fps",
        "platform",
        "detector",
    ]

    def __init__(self, output_path=None):
        if output_path is None:
            output_path = os.path.join(
                os.path.dirname(__file__), "..", "profile_%s.csv"
                % time.strftime("%Y%m%d_%H%M%S")
            )
        self._path = os.path.abspath(output_path)
        self._file = open(self._path, "w", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=self.FIELDS)
        self._writer.writeheader()
        self._start = time.time()
        self._frame_count = 0
        self._last_log = 0.0
        self._fps = 0.0
        self._cpu_samples = []
        self._cpu_lock = threading.Lock()
        self._running = True
        self._sample_thread = threading.Thread(
            target=self._sample_cpu, daemon=True
        )
        self._sample_thread.start()

    def _sample_cpu(self):
        while self._running:
            with self._cpu_lock:
                self._cpu_samples.append(psutil.cpu_percent(interval=None))
            time.sleep(0.5)

    def tick(self, vision_stats=None):
        now = time.time()
        self._frame_count += 1
        elapsed = now - self._start

        interval = now - self._last_log
        if interval < 1.0:
            return

        with self._cpu_lock:
            cpu = (
                sum(self._cpu_samples) / len(self._cpu_samples)
                if self._cpu_samples
                else 0.0
            )
            self._cpu_samples.clear()

        mem = psutil.virtual_memory()
        self._fps = self._frame_count / max(0.001, elapsed)
        self._last_log = now

        row = {
            "timestamp": time.strftime("%H:%M:%S", time.localtime(now)),
            "elapsed_s": "%.2f" % elapsed,
            "fps": "%.1f" % self._fps,
            "cpu_pct": "%.1f" % cpu,
            "ram_pct": "%.1f" % mem.percent,
            "ram_mb": "%.0f" % (mem.used / 1048576),
            "detect_ms": "%.1f" % (vision_stats.get("detect_ms") or 0),
            "gesture_ms": "%.1f" % (vision_stats.get("gesture_ms") or 0),
            "faces": vision_stats.get("faces", 0) if vision_stats else 0,
            "hands": vision_stats.get("hands", 0) if vision_stats else 0,
            "capture_fps": "%.1f" % (
                vision_stats.get("capture_fps") or 0
            ),
            "platform": (vision_stats.get("platform") or "") if vision_stats else "",
            "detector": (vision_stats.get("detector") or "") if vision_stats else "",
        }
        self._writer.writerow(row)
        self._file.flush()

    def stop(self):
        self._running = False
        self._file.close()

    @property
    def path(self):
        return self._path
