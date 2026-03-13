from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import cv2
import mediapipe as mp
import numpy as np
import serial
from serial import SerialException

from .config import AppConfig


mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles


@dataclass(slots=True)
class FrameResult:
    frame: np.ndarray
    servo_angles: list[int]
    status_text: str


class SerialAngleSender:
    def __init__(self, port: str | None, baudrate: int, enabled: bool = True) -> None:
        self._port = port
        self._baudrate = baudrate
        self._enabled = enabled and bool(port)
        self._serial: serial.Serial | None = None
        self._last_payload: str | None = None

    def connect(self) -> None:
        if not self._enabled or not self._port:
            return

        try:
            self._serial = serial.Serial(self._port, self._baudrate, timeout=1)
        except SerialException as exc:
            raise RuntimeError(f"Unable to open serial port {self._port}: {exc}") from exc

    def send(self, servo_angles: Iterable[int]) -> None:
        if not self._enabled:
            return
        if self._serial is None:
            raise RuntimeError("Serial connection has not been opened.")

        payload = ",".join(str(int(angle)) for angle in servo_angles)
        if payload == self._last_payload:
            return

        self._serial.write(f"{payload}\n".encode("ascii"))
        self._last_payload = payload

    def close(self) -> None:
        if self._serial and self._serial.is_open:
            self._serial.close()


class GestureHandController:
    def __init__(self, config: AppConfig, serial_sender: SerialAngleSender) -> None:
        self.config = config
        self.serial_sender = serial_sender
        self._smoothed_angles = [
            finger.open_angle for finger in self.config.finger_servos
        ]

    def reset(self) -> None:
        self._smoothed_angles = [
            finger.open_angle for finger in self.config.finger_servos
        ]

    def create_tracker(self) -> mp_hands.Hands:
        return mp_hands.Hands(
            model_complexity=1,
            max_num_hands=self.config.max_num_hands,
            min_detection_confidence=self.config.detection_confidence,
            min_tracking_confidence=self.config.tracking_confidence,
        )

    def process_frame(
        self, frame: np.ndarray, results: mp_hands.Hands
    ) -> FrameResult:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        hand_results = results.process(rgb_frame)
        servo_angles = self._smoothed_angles.copy()
        status_text = "No hand detected"

        if hand_results.multi_hand_landmarks and hand_results.multi_handedness:
            matched = self._select_matching_hand(hand_results)
            if matched is not None:
                hand_landmarks, handedness = matched
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_styles.get_default_hand_landmarks_style(),
                    mp_styles.get_default_hand_connections_style(),
                )
                raw_angles = self._landmarks_to_servo_angles(hand_landmarks)
                servo_angles = self._smooth_angles(raw_angles)
                self.serial_sender.send(servo_angles)
                status_text = f"Tracking {handedness.classification[0].label} hand"

        self._draw_overlay(frame, servo_angles, status_text)
        return FrameResult(frame=frame, servo_angles=servo_angles, status_text=status_text)

    def _select_matching_hand(self, hand_results) -> tuple | None:
        target_label = self.config.handedness_label.lower()
        for hand_landmarks, handedness in zip(
            hand_results.multi_hand_landmarks, hand_results.multi_handedness
        ):
            label = handedness.classification[0].label.lower()
            if label == target_label:
                return hand_landmarks, handedness

        if hand_results.multi_hand_landmarks:
            return (
                hand_results.multi_hand_landmarks[0],
                hand_results.multi_handedness[0],
            )
        return None

    def _landmarks_to_servo_angles(self, hand_landmarks) -> list[int]:
        landmarks = hand_landmarks.landmark

        finger_joint_triplets = [
            (1, 2, 4),
            (5, 6, 8),
            (9, 10, 12),
            (13, 14, 16),
            (17, 18, 20),
        ]

        servo_angles: list[int] = []
        for finger_cfg, (root_idx, mid_idx, tip_idx) in zip(
            self.config.finger_servos, finger_joint_triplets
        ):
            curl = self._normalized_joint_curl(
                landmarks[root_idx], landmarks[mid_idx], landmarks[tip_idx]
            )
            servo_angle = self._map_curl_to_servo(
                curl, finger_cfg.open_angle, finger_cfg.closed_angle
            )
            servo_angles.append(servo_angle)

        return servo_angles

    @staticmethod
    def _normalized_joint_curl(a, b, c) -> float:
        point_a = np.array([a.x, a.y, a.z], dtype=np.float32)
        point_b = np.array([b.x, b.y, b.z], dtype=np.float32)
        point_c = np.array([c.x, c.y, c.z], dtype=np.float32)

        ba = point_a - point_b
        bc = point_c - point_b

        ba_norm = np.linalg.norm(ba)
        bc_norm = np.linalg.norm(bc)
        if ba_norm == 0 or bc_norm == 0:
            return 0.0

        cosine_angle = np.dot(ba, bc) / (ba_norm * bc_norm)
        cosine_angle = float(np.clip(cosine_angle, -1.0, 1.0))
        angle = np.degrees(np.arccos(cosine_angle))

        # Open fingers tend toward ~180 degrees and closed fingers toward smaller angles.
        normalized = (180.0 - angle) / 120.0
        return float(np.clip(normalized, 0.0, 1.0))

    @staticmethod
    def _map_curl_to_servo(curl: float, open_angle: int, closed_angle: int) -> int:
        angle = open_angle + (closed_angle - open_angle) * curl
        return int(np.clip(round(angle), min(open_angle, closed_angle), max(open_angle, closed_angle)))

    def _smooth_angles(self, raw_angles: list[int]) -> list[int]:
        alpha = self.config.smoothing_factor
        smoothed: list[int] = []
        for current, target in zip(self._smoothed_angles, raw_angles):
            blended = round((1 - alpha) * current + alpha * target)
            smoothed.append(int(blended))
        self._smoothed_angles = smoothed
        return smoothed

    def _draw_overlay(self, frame: np.ndarray, servo_angles: list[int], status_text: str) -> None:
        cv2.rectangle(frame, (10, 10), (420, 185), (15, 15, 15), -1)
        cv2.putText(
            frame,
            "Robotic Hand Controller",
            (25, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            status_text,
            (25, 72),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 220, 255),
            2,
            cv2.LINE_AA,
        )

        for index, (finger_cfg, angle) in enumerate(
            zip(self.config.finger_servos, servo_angles), start=1
        ):
            cv2.putText(
                frame,
                f"{finger_cfg.name.title():<6}: {angle:>3} deg",
                (25, 72 + index * 22),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (180, 255, 180),
                1,
                cv2.LINE_AA,
            )
