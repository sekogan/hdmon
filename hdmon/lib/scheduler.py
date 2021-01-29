from dataclasses import dataclass
from typing import Dict, Callable, Optional
import heapq
import itertools
import threading
import time


Callback = Callable[[], None]  # Shouldn't raise exceptions
TimerId = int


@dataclass(order=True)
class _Timer:
    fire_time: float
    timer_id: TimerId
    callback: Optional[Callback]
    deleted = False


class Scheduler:
    def __init__(self):
        self._queue = []
        self._timer_by_id: Dict[TimerId, _Timer] = {}
        self._counter = itertools.count()
        self._stop_event = threading.Event()

    def set_timer(self, delay: float, callback: Callback) -> TimerId:
        assert delay >= 0
        timer_id = next(self._counter)
        timer = _Timer(
            fire_time=time.monotonic() + delay, timer_id=timer_id, callback=callback
        )
        heapq.heappush(self._queue, timer)
        return timer_id

    def clear_timer(self, timer_id: TimerId):
        timer = self._timer_by_id.pop(timer_id)
        timer.deleted = True
        timer.callback = None

    def run(self):
        while self._queue:
            timer = heapq.heappop(self._queue)
            if timer.deleted:
                continue
            delay = timer.fire_time - time.monotonic()
            if delay > 0:
                if self._stop_event.wait(delay):
                    break
                if timer.deleted:
                    continue
            timer.callback()

    def stop(self):
        self._stop_event.set()
