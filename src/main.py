from __future__ import annotations

import argparse

import cv2

from .config import AppConfig
from .gesture_controller import GestureHandController, SerialAngleSender

DEFAULT_ARDUINO_PORT = "COM4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Control a 5-finger robotic hand using MediaPipe hand tracking."
    )
    parser.add_argument(
        "--port",
        type=str,
        default=DEFAULT_ARDUINO_PORT,
        help=f"Arduino serial port, e.g. COM4 (default: {DEFAULT_ARDUINO_PORT})",
    )
    parser.add_argument("--baudrate", type=int, default=115200, help="Serial baudrate")
    parser.add_argument("--camera", type=int, default=0, help="Webcam index")
    parser.add_argument(
        "--left-hand",
        action="store_true",
        help="Track the left hand instead of the default right hand",
    )
    parser.add_argument(
        "--no-serial",
        action="store_true",
        help="Run vision-only mode without sending commands to Arduino",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.no_serial and not args.port:
        raise ValueError("Provide --port COMx or use --no-serial for camera-only mode.")

    config = AppConfig(
        camera_index=args.camera,
        serial_baudrate=args.baudrate,
        handedness_label="Left" if args.left_hand else "Right",
    )

    serial_sender = SerialAngleSender(
        port=args.port,
        baudrate=config.serial_baudrate,
        enabled=not args.no_serial,
    )

    if not args.no_serial:
        serial_sender.connect()

    capture = cv2.VideoCapture(config.camera_index)
    if not capture.isOpened():
        raise RuntimeError(f"Unable to open camera index {config.camera_index}.")

    capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)

    controller = GestureHandController(config, serial_sender)

    try:
        with controller.create_tracker() as tracker:
            while True:
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("Failed to read a frame from the webcam.")

                frame = cv2.flip(frame, 1)
                result = controller.process_frame(frame, tracker)
                cv2.imshow(config.display_window_name, result.frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key == ord("r"):
                    controller.reset()
    finally:
        capture.release()
        serial_sender.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
