# AI Gesture-Controlled 3D Printed Robotic Hand
PROJECT VIDEO LINK : https://www.youtube.com/shorts/FR_Llsw5JAc
This project mirrors a human hand in real time using:

- `MediaPipe` for webcam hand tracking
- `PySerial` for communication with an `Arduino Uno`
- `Servo` motors to actuate a 3D printed 5-finger robotic hand

The Python app reads hand landmarks, estimates finger bend values, and sends five angles over serial. The Arduino receives those angles and drives one servo per finger.

## Project Structure

```text
Hand_gesture/
|- arduino/
|  `- robotic_hand/
|     `- robotic_hand.ino
|- src/
|  |- config.py
|  |- gesture_controller.py
|  `- main.py
|- requirements.txt
`- README.md
```

## Hardware Required

- Arduino Uno
- 5 servo motors (SG90 or similar)
- 3D printed robotic hand with tendon or linkage mechanism
- External 5V power supply for servos
- Jumper wires
- USB cable for Arduino
- Webcam

## Wiring

Default servo pins in the Arduino sketch:

- Thumb: `3`
- Index: `5`
- Middle: `6`
- Ring: `9`
- Pinky: `10`

Important:

- Connect servo signal wires to the pins above.
- Connect all servo grounds to Arduino `GND`.
- Use a dedicated `5V` supply for the servos if possible.
- Connect the external power supply ground to Arduino ground.
- Do not power multiple servos directly from the Arduino 5V pin under load.

## Python Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Find your Arduino serial port, for example `COM4`.
4. Run:

```powershell
python -m src.main --port COM4
```

If you want to test without hardware:

```powershell
python -m src.main --no-serial
```

## Controls

- Press `q` to quit.
- Press `r` to reset smoothing history.
- Use `--camera 0` to select the webcam index.
- Use `--left-hand` if you want to mirror a left hand instead of the default right hand.

## Serial Protocol

The Python app sends one line per frame:

```text
<thumb>,<index>,<middle>,<ring>,<pinky>\n
```

Example:

```text
25,80,92,75,60
```

Each value is a servo target angle in degrees.

## Calibration Notes

Every robotic hand is mechanically different, so you may need to tune:

- servo min and max angles in `arduino/robotic_hand/robotic_hand.ino`
- smoothing and bend sensitivity in `src/config.py`

Start with slow movements and verify each finger direction before full-range motion.

## How It Works

1. `MediaPipe` detects 21 hand landmarks from the webcam.
2. The Python app computes finger curl from landmark joint angles.
3. Curl values are converted into servo angles.
4. Angles are sent to the Arduino over serial.
5. The Arduino updates the five servos to mimic the detected pose.

## Troubleshooting

### No serial connection

- Make sure the Arduino IDE serial monitor is closed.
- Verify the correct `COM` port.
- Reconnect the board and run again.

### Servos jitter or reset

- Use a separate power supply for the servos.
- Ensure all grounds are common.
- Increase smoothing in `src/config.py`.

### Wrong finger movement

- Reverse min and max servo values for that finger in the Arduino sketch.
- Check tendon routing and horn alignment.

## Future Improvements

- Gesture classification for predefined commands
- PID or trajectory smoothing on the Arduino side
- Dual-hand support
- ROS or MQTT integration
- Force feedback or grip detection
