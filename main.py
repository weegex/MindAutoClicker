from random import uniform
from time import sleep, time

from collections import deque
from dataclasses import dataclass

from threading import Thread
from threading import Lock as ThreadLock

from pynput import mouse
from uiautomation import (
    Click,
    RightClick
)


@dataclass
class ClickTimes:
    left: deque
    right: deque


@dataclass
class AutoClickStatus:
    left: bool
    right: bool


@dataclass
class AutoClickerWorkStatus:
   left: bool
   right: bool


@dataclass
class ThreadLocks:
    clickng_filter: ThreadLock
    left_auto_clicker: ThreadLock
    right_auto_clicker: ThreadLock


@dataclass
class LastEmulatedClickTimes:
    left: float
    right: float


KPS_THRESHOLD = 6
DEFAULT_DELAY = 80
DEFAULT_MAX_RANDOM_ADDITION = 40

delay = float(input(f"Введите базовую задержку между кликами ({DEFAULT_DELAY} мс): ") or DEFAULT_DELAY) * 0.001
max_random_addition = float(input(f"Введите максимальную случайную добавку ({DEFAULT_MAX_RANDOM_ADDITION} мс): ") or DEFAULT_MAX_RANDOM_ADDITION) * 0.001


class MindAutoClicker:
    def __init__(self):
        self.__click_times = ClickTimes(
            left=deque(),
            right=deque()
        )
        self.__auto_click_status = AutoClickStatus(
            left=False,
            right=False
        )
        self.__auto_clicker = AutoClickerWorkStatus(
            left=False,
            right=False
        )
        self.__thread_lock = ThreadLocks(
            clickng_filter=ThreadLock(),
            left_auto_clicker=ThreadLock(),
            right_auto_clicker=ThreadLock()
        )

        self.__last_emulated = LastEmulatedClickTimes(
            left=0.0,
            right=0.0
        )
        self._emulated_epsilon = 0.005
        
        self.__mouse_controller = mouse.Controller()

    def start(self):
        Thread(target=self.update_kps, daemon=True).start()
        Thread(target=self.left_auto_clicker_worker, daemon=True).start()
        Thread(target=self.right_auto_clicker_worker, daemon=True).start()

        listener = mouse.Listener(on_click=self.on_click)
        listener.start()

        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            listener.stop()

    def on_click(
        self, 
        _,
        __,
        button: mouse.Button,
        pressed: bool
    ):
        if not pressed: return

        with self.__thread_lock.clickng_filter:
            now = time()

            if button == mouse.Button.left:
                if now - self.__last_emulated.left < self._emulated_epsilon: return
                self.__click_times.left.append(time())
            elif button == mouse.Button.right:
                if now - self.__last_emulated.right < self._emulated_epsilon: return
                self.__click_times.right.append(time())

    def filter_click_times_deque(
        self,
        click_times_deque: deque,
        current_time: float
    ) -> deque:
        while click_times_deque and click_times_deque[0] < current_time - 1.0:
            click_times_deque.popleft()

        return click_times_deque

    def update_kps(self):
        while True:
            current_time = time()

            with self.__thread_lock.clickng_filter:
                self.filter_click_times_deque(self.__click_times.left, current_time)
                self.filter_click_times_deque(self.__click_times.right, current_time)
                
                left_kps = len(self.__click_times.left)
                right_kps = len(self.__click_times.right)
            print(f"\rKPS: {left_kps}/{right_kps}", end="", flush=True)

            with self.__thread_lock.left_auto_clicker:
                should_enable = len(self.__click_times.left) >= KPS_THRESHOLD

                if should_enable != self.__auto_clicker.left:
                    self.__auto_clicker.left = should_enable

            with self.__thread_lock.right_auto_clicker:
                should_enable = len(self.__click_times.right) >= KPS_THRESHOLD

                if should_enable != self.__auto_clicker.right:
                    self.__auto_clicker.right = should_enable
            
            sleep(0.1)

    def left_auto_clicker_worker(self):
        while True:
            with self.__thread_lock.left_auto_clicker:
                enabled = self.__auto_clicker.left
            
            if enabled:
                current_delay = delay + uniform(0, max_random_addition)

                with self.__thread_lock.clickng_filter:
                    self.__last_emulated.left = time()

                Click(
                    self.__mouse_controller.position[0],
                    self.__mouse_controller.position[1],
                    current_delay
                )
            else:
                sleep(0.01)

    def right_auto_clicker_worker(self):
        while True:
            with self.__thread_lock.right_auto_clicker:
                enabled = self.__auto_clicker.right
            
            if enabled:
                current_delay = delay + uniform(0, max_random_addition)

                with self.__thread_lock.clickng_filter:
                    self.__last_emulated.right = time()

                RightClick(
                    self.__mouse_controller.position[0],
                    self.__mouse_controller.position[1],
                    current_delay
                )
            else:
                sleep(0.01)


if __name__ == "__main__":
    auto_clicker = MindAutoClicker()
    auto_clicker.start()
