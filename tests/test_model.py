import unittest

from experiencebar.model import State, xp_required_for_level


class ModelTest(unittest.TestCase):
    def test_level_curve_increases(self) -> None:
        self.assertEqual(xp_required_for_level(1), 100)
        self.assertGreater(xp_required_for_level(2), xp_required_for_level(1))
        self.assertGreater(xp_required_for_level(10), xp_required_for_level(2))

    def test_gain_xp_tracks_current_level_and_lifetime(self) -> None:
        state = State()

        levels = state.gain_xp(125)

        self.assertEqual(levels, [2])
        self.assertEqual(state.level, 2)
        self.assertEqual(state.current_xp, 25)
        self.assertEqual(state.lifetime_xp, 125)

    def test_task_completion_awards_difficulty_xp_once(self) -> None:
        state = State()
        task = state.add_task("Finish draft", "hard")

        completed, levels = state.complete_task(task.id)

        self.assertTrue(completed.is_complete)
        self.assertEqual(levels, [2])
        self.assertEqual(state.level, 2)
        self.assertEqual(state.current_xp, 20)
        self.assertEqual(state.lifetime_xp, 120)


if __name__ == "__main__":
    unittest.main()
