from dataclasses import dataclass, field


@dataclass(slots=True)
class FingerServoConfig:
    name: str
    open_angle: int
    closed_angle: int


@dataclass(slots=True)
class AppConfig:
    camera_index: int = 0
    frame_width: int = 1280
    frame_height: int = 720
    max_num_hands: int = 1
    detection_confidence: float = 0.7
    tracking_confidence: float = 0.7
    smoothing_factor: float = 0.35
    serial_baudrate: int = 115200
    display_window_name: str = "AI Gesture-Controlled Robotic Hand"
    handedness_label: str = "Right"
    finger_servos: list[FingerServoConfig] = field(
        default_factory=lambda: [
            FingerServoConfig("thumb", open_angle=10, closed_angle=105),
            FingerServoConfig("index", open_angle=15, closed_angle=120),
            FingerServoConfig("middle", open_angle=15, closed_angle=120),
            FingerServoConfig("ring", open_angle=20, closed_angle=125),
            FingerServoConfig("pinky", open_angle=25, closed_angle=130),
        ]
    )
