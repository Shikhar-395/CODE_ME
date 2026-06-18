import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from backend.docker_executor import (
    DockerSettings,
    build_docker_command,
    build_job_payload,
    execute_in_docker,
)
from backend.model import SubmissionStatus


class DockerCommandTests(unittest.TestCase):
    def test_command_applies_required_isolation(self):
        settings = DockerSettings()

        command = build_docker_command(settings, "judge-test")

        self.assertIn("--network", command)
        self.assertEqual(command[command.index("--network") + 1], "none")
        self.assertIn("--read-only", command)
        self.assertIn("--cap-drop", command)
        self.assertEqual(command[command.index("--cap-drop") + 1], "ALL")
        self.assertIn("no-new-privileges=true", command)
        self.assertIn("--pids-limit", command)
        self.assertIn("--memory", command)
        self.assertIn("--memory-swap", command)
        self.assertIn("--cpus", command)
        self.assertIn("--user", command)
        self.assertEqual(command[command.index("--user") + 1], "65532:65532")
        self.assertNotIn("--privileged", command)

    def test_payload_contains_code_and_test_cases(self):
        submission = SimpleNamespace(
            language=SimpleNamespace(value="python"),
            code="print(input())",
        )
        test_cases = [
            SimpleNamespace(input_data="hello\n", output_data="hello\n"),
        ]

        payload = build_job_payload(submission, test_cases)

        self.assertEqual(payload["language"], "python")
        self.assertEqual(payload["code"], "print(input())")
        self.assertEqual(
            payload["test_cases"],
            [{"input": "hello\n", "expected_output": "hello\n"}],
        )


class DockerExecutionTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_container_result_is_converted_to_submission_status(self):
        process = _FakeProcess(
            stdout=json.dumps(
                {
                    "status": "accepted",
                    "output": "",
                    "error": "",
                }
            ).encode(),
            stderr=b"",
            returncode=0,
        )
        submission = SimpleNamespace(
            id=7,
            language="python",
            code="print(1)",
        )
        test_cases = [
            SimpleNamespace(input_data="", output_data="1\n"),
        ]

        with (
            patch(
                "backend.docker_executor.asyncio.create_subprocess_exec",
                new=AsyncMock(return_value=process),
            ),
            patch(
                "backend.docker_executor._remove_container",
                new=AsyncMock(),
            ),
        ):
            result = await execute_in_docker(
                submission,
                test_cases,
                settings=DockerSettings(binary="/bin/echo"),
            )

        self.assertEqual(result["status"], SubmissionStatus.ACCEPTED)
        sent_payload = json.loads(process.input_data)
        self.assertEqual(sent_payload["language"], "python")


class _FakeProcess:
    def __init__(self, stdout, stderr, returncode):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        self.input_data = None

    async def communicate(self, input_data):
        self.input_data = input_data
        return self.stdout, self.stderr


if __name__ == "__main__":
    unittest.main()
