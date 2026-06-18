import asyncio
import json
import os
import shutil
import uuid
from dataclasses import dataclass
from typing import Any

from .model import SubmissionStatus


MAX_REQUEST_BYTES = 8 * 1024 * 1024
MAX_RESPONSE_BYTES = 1024 * 1024


class DockerExecutionError(RuntimeError):
    """Raised when a judge container cannot start or return a valid result."""


@dataclass(frozen=True)
class DockerSettings:
    binary: str = "docker"
    image: str = "leetcode-judge:latest"
    memory: str = "512m"
    cpus: str = "1.0"
    pids_limit: int = 128
    tmpfs_size: str = "384m"
    job_timeout_seconds: float = 45.0

    @classmethod
    def from_environment(cls) -> "DockerSettings":
        return cls(
            binary=os.getenv("DOCKER_BIN", "docker"),
            image=os.getenv("JUDGE_DOCKER_IMAGE", "leetcode-judge:latest"),
            memory=os.getenv("JUDGE_DOCKER_MEMORY", "512m"),
            cpus=os.getenv("JUDGE_DOCKER_CPUS", "1.0"),
            pids_limit=int(os.getenv("JUDGE_DOCKER_PIDS_LIMIT", "128")),
            tmpfs_size=os.getenv("JUDGE_DOCKER_TMPFS_SIZE", "384m"),
            job_timeout_seconds=float(
                os.getenv("JUDGE_DOCKER_TIMEOUT_SECONDS", "45")
            ),
        )

    def validate(self) -> None:
        if not _binary_exists(self.binary):
            raise DockerExecutionError(
                f"Docker binary was not found: {self.binary}"
            )
        if not self.image:
            raise DockerExecutionError("JUDGE_DOCKER_IMAGE cannot be empty.")
        if self.pids_limit < 16:
            raise DockerExecutionError(
                "JUDGE_DOCKER_PIDS_LIMIT must be at least 16."
            )
        if self.job_timeout_seconds <= 0:
            raise DockerExecutionError(
                "JUDGE_DOCKER_TIMEOUT_SECONDS must be greater than zero."
            )


def _binary_exists(binary: str) -> bool:
    if "/" in binary:
        return os.path.isfile(binary) and os.access(binary, os.X_OK)
    return shutil.which(binary) is not None


def build_job_payload(
    submission: Any,
    test_cases: list[Any],
) -> dict[str, Any]:
    language = getattr(submission.language, "value", submission.language)
    return {
        "language": str(language),
        "code": submission.code,
        "test_cases": [
            {
                "input": testcase.input_data,
                "expected_output": testcase.output_data,
            }
            for testcase in test_cases
        ],
        "limits": {
            "compile_timeout_seconds": 10,
            "run_timeout_seconds": 5,
            "output_bytes": 1024 * 1024,
        },
    }


def build_docker_command(
    settings: DockerSettings,
    container_name: str,
) -> list[str]:
    return [
        settings.binary,
        "run",
        "--rm",
        "--interactive",
        "--name",
        container_name,
        "--pull",
        "never",
        "--network",
        "none",
        "--memory",
        settings.memory,
        "--memory-swap",
        settings.memory,
        "--cpus",
        settings.cpus,
        "--pids-limit",
        str(settings.pids_limit),
        "--read-only",
        "--tmpfs",
        f"/tmp:rw,nosuid,nodev,exec,size={settings.tmpfs_size}",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges=true",
        "--user",
        "65532:65532",
        "--ulimit",
        "nofile=64:64",
        "--init",
        settings.image,
    ]


async def execute_in_docker(
    submission: Any,
    test_cases: list[Any],
    settings: DockerSettings | None = None,
) -> dict[str, Any]:
    settings = settings or DockerSettings.from_environment()
    settings.validate()

    payload = json.dumps(
        build_job_payload(submission, test_cases),
        separators=(",", ":"),
    ).encode()
    if len(payload) > MAX_REQUEST_BYTES:
        raise DockerExecutionError(
            f"Submission payload exceeds {MAX_REQUEST_BYTES} bytes."
        )

    submission_id = getattr(submission, "id", "unknown")
    container_name = (
        f"leetcode-judge-{submission_id}-{uuid.uuid4().hex[:10]}"
    )
    command = build_docker_command(settings, container_name)

    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(payload),
            timeout=settings.job_timeout_seconds,
        )
    except asyncio.TimeoutError as exc:
        if process.returncode is None:
            process.kill()
            await process.wait()
        await _remove_container(settings.binary, container_name)
        raise DockerExecutionError(
            "The judge container exceeded its host-side timeout."
        ) from exc
    except BaseException:
        if process.returncode is None:
            process.kill()
            await process.wait()
        await _remove_container(settings.binary, container_name)
        raise
    else:
        await _remove_container(settings.binary, container_name)

    stderr_text = stderr.decode(errors="replace").strip()
    if process.returncode != 0:
        raise DockerExecutionError(
            "Judge container failed"
            + (f": {stderr_text[:4096]}" if stderr_text else ".")
        )

    if len(stdout) > MAX_RESPONSE_BYTES:
        raise DockerExecutionError(
            f"Judge response exceeds {MAX_RESPONSE_BYTES} bytes."
        )

    try:
        response = json.loads(stdout)
        status = SubmissionStatus(response["status"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise DockerExecutionError(
            f"Judge container returned an invalid result: "
            f"{stdout[:4096]!r}"
        ) from exc

    return {
        "status": status,
        "output": response.get("output", ""),
        "error": response.get("error", ""),
    }


async def check_docker_image(
    settings: DockerSettings | None = None,
) -> None:
    settings = settings or DockerSettings.from_environment()
    settings.validate()

    process = await asyncio.create_subprocess_exec(
        settings.binary,
        "image",
        "inspect",
        settings.image,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        raise DockerExecutionError(
            f"Docker image {settings.image!r} is unavailable: "
            f"{stderr.decode(errors='replace').strip()}"
        )


async def _remove_container(binary: str, container_name: str) -> None:
    process = await asyncio.create_subprocess_exec(
        binary,
        "rm",
        "--force",
        container_name,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        await asyncio.wait_for(process.wait(), timeout=5)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
