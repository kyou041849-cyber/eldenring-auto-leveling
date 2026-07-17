import argparse
import signal
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import vgamepad as vg


BUTTON_MAP = {
    "Cross": vg.DS4_BUTTONS.DS4_BUTTON_CROSS,
    "Circle": vg.DS4_BUTTONS.DS4_BUTTON_CIRCLE,
    "Square": vg.DS4_BUTTONS.DS4_BUTTON_SQUARE,
    "Triangle": vg.DS4_BUTTONS.DS4_BUTTON_TRIANGLE,
    "L1": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_LEFT,
    "R1": vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT,
    "Share": vg.DS4_BUTTONS.DS4_BUTTON_SHARE,
    "Options": vg.DS4_BUTTONS.DS4_BUTTON_OPTIONS,
    "L3": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_LEFT,
    "R3": vg.DS4_BUTTONS.DS4_BUTTON_THUMB_RIGHT,
}

SPECIAL_BUTTON_MAP = {
    "PS": vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_PS,
    "TouchButton": vg.DS4_SPECIAL_BUTTONS.DS4_SPECIAL_BUTTON_TOUCHPAD,
}

DPAD_MAP = {
    (False, False, False, False): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE,
    (True, False, False, False): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTH,
    (False, True, False, False): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTH,
    (False, False, True, False): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST,
    (False, False, False, True): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_EAST,
    (True, False, True, False): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHWEST,
    (True, False, False, True): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NORTHEAST,
    (False, True, True, False): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHWEST,
    (False, True, False, True): vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_SOUTHEAST,
}


def xml_text(state, name, default="0"):
    node = state.find(name)
    return node.text if node is not None and node.text is not None else default


def parse_timestamp(value):
    return datetime.fromisoformat(value.rstrip("Z"))


def axis(value, scale=1.0, deadzone=0.0):
    normalized = (value - 128) / 127.0
    normalized = max(-1.0, min(1.0, normalized * scale))
    return 0.0 if abs(normalized) < deadzone else normalized


def parse_states(path):
    root = ET.parse(path).getroot()
    states = []
    for state in root.findall("DualShockState"):
        up = xml_text(state, "DPad_Up", "false").lower() == "true"
        down = xml_text(state, "DPad_Down", "false").lower() == "true"
        left = xml_text(state, "DPad_Left", "false").lower() == "true"
        right = xml_text(state, "DPad_Right", "false").lower() == "true"
        states.append(
            {
                "timestamp": parse_timestamp(xml_text(state, "ReportTimeStamp")),
                "lx": int(xml_text(state, "LX", "128")),
                "ly": int(xml_text(state, "LY", "128")),
                "rx": int(xml_text(state, "RX", "128")),
                "ry": int(xml_text(state, "RY", "128")),
                "l2": int(xml_text(state, "L2", "0")),
                "r2": int(xml_text(state, "R2", "0")),
                "dpad": DPAD_MAP.get(
                    (up, down, left, right),
                    vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE,
                ),
                "buttons": {
                    name: xml_text(state, name, "false").lower() == "true"
                    for name in BUTTON_MAP
                },
                "special_buttons": {
                    name: xml_text(state, name, "false").lower() == "true"
                    for name in SPECIAL_BUTTON_MAP
                },
            }
        )
    if not states:
        raise ValueError("No DualShockState entries found.")
    return states


def trim_at_last_cross_release(states, neutral_wait):
    if neutral_wait is None or neutral_wait < 0:
        return states, None

    first = states[0]["timestamp"]
    last_cross_release = None
    was_pressed = False
    for state in states:
        is_pressed = state["buttons"].get("Cross", False)
        if was_pressed and not is_pressed:
            last_cross_release = state["timestamp"]
        was_pressed = is_pressed

    if last_cross_release is None:
        return states, None

    cutoff_elapsed = (last_cross_release - first).total_seconds()
    trimmed = [
        state
        for state in states
        if (state["timestamp"] - first).total_seconds() <= cutoff_elapsed
    ]
    if not trimmed:
        return states, None

    return trimmed, {
        "last_cross_release": (last_cross_release - first).total_seconds(),
        "neutral_wait": neutral_wait,
        "cutoff_elapsed": cutoff_elapsed,
        "original_duration": (states[-1]["timestamp"] - first).total_seconds(),
        "trimmed_duration": (trimmed[-1]["timestamp"] - first).total_seconds(),
        "original_count": len(states),
        "trimmed_count": len(trimmed),
    }


class DS4Pad:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.gamepad = None if dry_run else vg.VDS4Gamepad()
        self.reset()

    def reset(self):
        if self.dry_run:
            return
        for button in BUTTON_MAP.values():
            self.gamepad.release_button(button)
        self.gamepad.release_button(vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_LEFT)
        self.gamepad.release_button(vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_RIGHT)
        for button in SPECIAL_BUTTON_MAP.values():
            self.gamepad.release_special_button(button)
        self.gamepad.directional_pad(vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE)
        self.gamepad.left_trigger(value=0)
        self.gamepad.right_trigger(value=0)
        self.gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
        self.gamepad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
        self.gamepad.update()

    def neutral_flush(self, duration=0.6, interval=0.05):
        if self.dry_run:
            return
        end = time.perf_counter() + duration
        while time.perf_counter() < end:
            self.reset()
            time.sleep(interval)

    def apply_state(self, state, elapsed, args):
        if self.dry_run:
            return

        left_enabled = (
            args.disable_left_stick_after is None
            or elapsed < args.disable_left_stick_after
        )
        right_enabled = (
            args.disable_right_stick_after is None
            or elapsed < args.disable_right_stick_after
        )

        for source_name, target_button in BUTTON_MAP.items():
            if state["buttons"][source_name]:
                self.gamepad.press_button(target_button)
            else:
                self.gamepad.release_button(target_button)

        for source_name, target_button in SPECIAL_BUTTON_MAP.items():
            if state["special_buttons"][source_name]:
                self.gamepad.press_special_button(target_button)
            else:
                self.gamepad.release_special_button(target_button)

        if state["l2"] > 0:
            self.gamepad.press_button(vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_LEFT)
        else:
            self.gamepad.release_button(vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_LEFT)
        if state["r2"] > 0:
            self.gamepad.press_button(vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_RIGHT)
        else:
            self.gamepad.release_button(vg.DS4_BUTTONS.DS4_BUTTON_TRIGGER_RIGHT)

        self.gamepad.directional_pad(state["dpad"])
        self.gamepad.left_trigger(value=state["l2"])
        self.gamepad.right_trigger(value=state["r2"])
        self.gamepad.left_joystick_float(
            x_value_float=axis(
                state["lx"],
                scale=args.left_stick_x_scale,
                deadzone=args.deadzone,
            )
            if left_enabled
            else 0.0,
            y_value_float=axis(
                state["ly"],
                scale=args.left_stick_y_scale,
                deadzone=args.deadzone,
            )
            if left_enabled
            else 0.0,
        )
        self.gamepad.right_joystick_float(
            x_value_float=axis(
                state["rx"],
                scale=args.right_stick_x_scale,
                deadzone=args.deadzone,
            )
            if right_enabled
            else 0.0,
            y_value_float=axis(
                state["ry"],
                scale=args.right_stick_y_scale,
                deadzone=args.deadzone,
            )
            if right_enabled
            else 0.0,
        )
        self.gamepad.update()


def summarize(states, args, trim_info=None):
    first = states[0]["timestamp"]
    last = states[-1]["timestamp"]
    print(f"Loaded {len(states)} states")
    print(f"Duration: {(last - first).total_seconds():.3f}s")
    print("Controller mode: virtual DS4")
    print(f"Deadzone: {args.deadzone:.2f}")
    if trim_info is not None:
        print(
            "Tail trim: replay stops at "
            f"last Cross release {trim_info['last_cross_release']:.3f}s, "
            f"then neutral wait {trim_info['neutral_wait']:.1f}s"
        )
        print(
            "Original XML: "
            f"{trim_info['original_count']} states / "
            f"{trim_info['original_duration']:.3f}s"
        )
    if args.disable_left_stick_after is not None:
        print(f"Left stick will be neutral after {args.disable_left_stick_after:.3f}s")
    if args.disable_right_stick_after is not None:
        print(f"Right stick will be neutral after {args.disable_right_stick_after:.3f}s")

    previous = None
    for state in states:
        current = {
            "buttons": tuple(
                name for name, is_pressed in state["buttons"].items() if is_pressed
            ),
            "special": tuple(
                name
                for name, is_pressed in state["special_buttons"].items()
                if is_pressed
            ),
            "dpad": state["dpad"],
            "l2": state["l2"] > 0,
            "r2": state["r2"] > 0,
            "left": (
                abs(axis(state["lx"], deadzone=args.deadzone)) > 0,
                abs(axis(state["ly"], deadzone=args.deadzone)) > 0,
            ),
            "right": (
                abs(axis(state["rx"], deadzone=args.deadzone)) > 0,
                abs(axis(state["ry"], deadzone=args.deadzone)) > 0,
            ),
        }
        if current != previous:
            elapsed = (state["timestamp"] - first).total_seconds()
            pressed = list(current["buttons"]) + list(current["special"])
            if current["dpad"] != vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE:
                pressed.append("DPad")
            if current["l2"]:
                pressed.append("L2")
            if current["r2"]:
                pressed.append("R2")
            if any(current["left"]):
                pressed.append(f"LS({state['lx']},{state['ly']})")
            if any(current["right"]):
                pressed.append(f"RS({state['rx']},{state['ry']})")
            label = ", ".join(pressed) if pressed else "neutral"
            print(f"{elapsed:7.3f}s  {label}")
            previous = current


def replay(states, args):
    stop = False

    def on_stop(_signum, _frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, on_stop)

    def sleep_until(target_time):
        while not stop:
            remaining = target_time - time.perf_counter()
            if remaining <= 0:
                return
            time.sleep(min(remaining, 0.05))

    pad = DS4Pad(dry_run=args.dry_run)
    first = states[0]["timestamp"]
    duration = (states[-1]["timestamp"] - first).total_seconds()
    try:
        loop = 0
        while not stop and (args.loops == 0 or loop < args.loops):
            loop += 1
            print(f"\nReplay loop {loop}")
            loop_started = time.perf_counter()
            for state in states:
                if stop:
                    break
                target = (state["timestamp"] - first).total_seconds() / args.speed
                sleep_until(loop_started + target)
                if stop:
                    break
                elapsed = (state["timestamp"] - first).total_seconds()
                pad.apply_state(state, elapsed, args)
            if stop:
                break
            pad.neutral_flush(args.neutral_flush)
            if (
                args.after_last_cross_neutral_wait > 0
                and not stop
                and (args.loops == 0 or loop <= args.loops)
            ):
                print(f"  neutral wait {args.after_last_cross_neutral_wait:.1f}s")
                pad.neutral_flush(args.after_last_cross_neutral_wait)
            if args.loop_gap > 0 and not stop and (args.loops == 0 or loop < args.loops):
                print(f"  loop gap {args.loop_gap:.1f}s")
                sleep_until(time.perf_counter() + args.loop_gap)
            print(f"  loop duration target {duration:.3f}s")
    finally:
        if stop:
            print(f"\nCtrl+C received. Holding neutral for {args.interrupt_neutral_wait:.1f}s before exit.")
            pad.neutral_flush(args.interrupt_neutral_wait)
            print("Stopped. Controller held neutral before exit.")
        else:
            pad.neutral_flush(args.neutral_flush)
            print("\nStopped. Controller returned to neutral.")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Replay a PS4 Macro DualShockState XML through a virtual DS4 controller."
    )
    parser.add_argument("--xml", required=True, help="Path to PS4 Macro XML file.")
    parser.add_argument("--loops", type=int, default=1, help="0 means infinite.")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--loop-gap", type=float, default=0.0)
    parser.add_argument("--deadzone", type=float, default=0.0)
    parser.add_argument("--neutral-flush", type=float, default=0.6)
    parser.add_argument(
        "--interrupt-neutral-wait",
        type=float,
        default=3.0,
        help="When Ctrl+C is pressed, hold the virtual controller neutral for this many seconds before exiting.",
    )
    parser.add_argument(
        "--after-last-cross-neutral-wait",
        type=float,
        default=3.0,
        help="Stop XML replay at the final Cross release, then wait neutral for this many seconds. Use -1 for full XML.",
    )
    parser.add_argument("--left-stick-x-scale", type=float, default=1.0)
    parser.add_argument("--left-stick-y-scale", type=float, default=1.0)
    parser.add_argument("--right-stick-x-scale", type=float, default=1.0)
    parser.add_argument("--right-stick-y-scale", type=float, default=1.0)
    parser.add_argument(
        "--disable-left-stick-after",
        type=float,
        default=None,
        help="Keep the left stick neutral after this XML timestamp in seconds.",
    )
    parser.add_argument(
        "--disable-right-stick-after",
        type=float,
        default=None,
        help="Keep the right stick neutral after this XML timestamp in seconds.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


if __name__ == "__main__":
    options = parse_args(sys.argv[1:])
    macro_states = parse_states(options.xml)
    macro_states, tail_trim = trim_at_last_cross_release(
        macro_states,
        options.after_last_cross_neutral_wait,
    )
    summarize(macro_states, options, tail_trim)
    if options.dry_run:
        print("\nDry-run only. No controller input was sent.")
    else:
        replay(macro_states, options)
