import tempfile
import unittest
from pathlib import Path

from experiencebar.model import State
from experiencebar.storage import load_state, save_state


class StorageTest(unittest.TestCase):
    def test_state_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            state = State()
            state.add_task("Plan sprint", "medium")
            state.gain_xp(42)

            save_state(path, state)
            loaded = load_state(path)

        self.assertEqual(loaded.level, state.level)
        self.assertEqual(loaded.current_xp, 42)
        self.assertEqual(loaded.tasks[0].title, "Plan sprint")


if __name__ == "__main__":
    unittest.main()
