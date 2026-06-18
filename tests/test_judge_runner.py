import unittest

from docker.judge.runner import judge


class JudgeRunnerTests(unittest.TestCase):
    def test_python_submission_is_accepted(self):
        result = judge(
            {
                "language": "python",
                "code": "a, b = map(int, input().split())\nprint(a + b)\n",
                "test_cases": [
                    {"input": "2 3\n", "expected_output": "5\n"},
                    {"input": "10 -4\n", "expected_output": "6\n"},
                ],
                "limits": {"run_timeout_seconds": 1},
            }
        )

        self.assertEqual(result["status"], "accepted")

    def test_wrong_answer_is_reported(self):
        result = judge(
            {
                "language": "python",
                "code": "print(7)\n",
                "test_cases": [{"input": "", "expected_output": "8\n"}],
            }
        )

        self.assertEqual(result["status"], "wrong_answer")

    def test_timeout_is_reported(self):
        result = judge(
            {
                "language": "python",
                "code": "while True:\n    pass\n",
                "test_cases": [{"input": "", "expected_output": ""}],
                "limits": {"run_timeout_seconds": 0.1},
            }
        )

        self.assertEqual(result["status"], "tle")


if __name__ == "__main__":
    unittest.main()
