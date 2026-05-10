from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from experiencebar.model import DIFFICULTY_XP, State
from experiencebar.storage import default_state_file, load_state, save_state

DEFAULT_XP_PER_MINUTE = 6
DEFAULT_TICK_SECONDS = 10


def format_status(state: State) -> str:
    percent = round(state.progress_ratio * 100)
    return (
        f"Level {state.level} | XP {state.current_xp}/{state.xp_needed} | "
        f"{percent}% | Lifetime {state.lifetime_xp}"
    )


def print_level_ups(levels: list[int]) -> None:
    for level in levels:
        print(f"Level up! You reached level {level}.")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="experiencebar",
        description="Run an MMORPG-style terminal XP bar while you work.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=default_state_file(),
        help="Path to the JSON state file.",
    )

    subparsers = parser.add_subparsers(dest="command")

    work = subparsers.add_parser("work", help="Earn XP over time while working.")
    work.add_argument("--minutes", type=float, help="Stop automatically after this many minutes.")
    work.add_argument("--xp-per-minute", type=int, default=DEFAULT_XP_PER_MINUTE)
    work.add_argument("--tick-seconds", type=float, default=DEFAULT_TICK_SECONDS)

    gain = subparsers.add_parser("gain", help="Award XP immediately.")
    gain.add_argument("amount", type=int)
    gain.add_argument("--reason", default="")

    subparsers.add_parser("status", help="Show current level progress.")

    task = subparsers.add_parser("task", help="Manage difficulty-based tasks.")
    task_subparsers = task.add_subparsers(dest="task_command", required=True)

    task_add = task_subparsers.add_parser("add", help="Add a task.")
    task_add.add_argument("title")
    task_add.add_argument("difficulty", choices=sorted(DIFFICULTY_XP))

    task_subparsers.add_parser("list", help="List tasks.")

    task_complete = task_subparsers.add_parser("complete", help="Complete a task and gain XP.")
    task_complete.add_argument("id", type=int)

    subparsers.add_parser("reset", help="Reset level, XP, and tasks.")

    return parser


def run_work(args: argparse.Namespace, state: State, state_file: Path) -> int:
    try:
        from tqdm import tqdm
    except ModuleNotFoundError as error:
        raise ValueError(
            "tqdm is required for work sessions. Install dependencies with `uv sync`."
        ) from error

    if args.xp_per_minute <= 0:
        raise ValueError("--xp-per-minute must be positive")
    if args.tick_seconds <= 0:
        raise ValueError("--tick-seconds must be positive")
    if args.minutes is not None and args.minutes <= 0:
        raise ValueError("--minutes must be positive")

    session_seconds = None if args.minutes is None else args.minutes * 60
    start = time.monotonic()
    xp_remainder = 0.0
    last_tick = start

    print("Working session started. Press Ctrl+C to stop and save progress.")

    try:
        while True:
            needed = state.xp_needed
            bar = tqdm(
                total=needed,
                initial=state.current_xp,
                desc=f"Level {state.level}",
                unit="xp",
                leave=True,
                dynamic_ncols=True,
                bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} xp",
            )

            while state.current_xp < needed:
                now = time.monotonic()
                elapsed = now - start
                if session_seconds is not None and elapsed >= session_seconds:
                    save_state(state_file, state)
                    bar.close()
                    print(format_status(state))
                    return 0

                sleep_for = args.tick_seconds
                if session_seconds is not None:
                    sleep_for = min(sleep_for, max(0.0, session_seconds - elapsed))
                time.sleep(sleep_for)

                tick_now = time.monotonic()
                tick_elapsed = tick_now - last_tick
                last_tick = tick_now
                raw_xp = (args.xp_per_minute / 60) * tick_elapsed + xp_remainder
                xp_gain = int(raw_xp)
                xp_remainder = raw_xp - xp_gain

                if xp_gain <= 0:
                    continue

                before = state.current_xp
                levels = state.gain_xp(xp_gain)
                save_state(state_file, state)
                bar.update(min(xp_gain, needed - before))
                if levels:
                    bar.close()
                    print_level_ups(levels)
                    break
            else:
                bar.close()
                levels = state.gain_xp(0)
                print_level_ups(levels)
    except KeyboardInterrupt:
        save_state(state_file, state)
        print()
        print(format_status(state))
        return 0


def run_gain(args: argparse.Namespace, state: State, state_file: Path) -> int:
    if args.amount < 0:
        raise ValueError("amount must be non-negative")
    levels = state.gain_xp(args.amount)
    save_state(state_file, state)
    reason = f" for {args.reason}" if args.reason else ""
    print(f"Gained {args.amount} XP{reason}.")
    print_level_ups(levels)
    print(format_status(state))
    return 0


def run_task(args: argparse.Namespace, state: State, state_file: Path) -> int:
    if args.task_command == "add":
        task = state.add_task(args.title, args.difficulty)
        save_state(state_file, state)
        print(f"Added task {task.id}: {task.title} [{task.difficulty}, {task.xp} XP]")
        return 0

    if args.task_command == "list":
        if not state.tasks:
            print("No tasks yet.")
            return 0
        for task in state.tasks:
            marker = "done" if task.is_complete else "todo"
            print(f"{task.id}. [{marker}] {task.title} ({task.difficulty}, {task.xp} XP)")
        return 0

    if args.task_command == "complete":
        task, levels = state.complete_task(args.id)
        save_state(state_file, state)
        print(f"Completed task {task.id}: {task.title}. Gained {task.xp} XP.")
        print_level_ups(levels)
        print(format_status(state))
        return 0

    raise ValueError(f"unknown task command: {args.task_command}")


def run(args: argparse.Namespace) -> int:
    state_file = args.state_file.expanduser()
    state = load_state(state_file)

    command = args.command or "work"
    if command == "work":
        if args.command is None:
            args.minutes = None
            args.xp_per_minute = DEFAULT_XP_PER_MINUTE
            args.tick_seconds = DEFAULT_TICK_SECONDS
        return run_work(args, state, state_file)
    if command == "gain":
        return run_gain(args, state, state_file)
    if command == "status":
        print(format_status(state))
        return 0
    if command == "task":
        return run_task(args, state, state_file)
    if command == "reset":
        save_state(state_file, State())
        print("Progress reset.")
        return 0

    raise ValueError(f"unknown command: {command}")


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
