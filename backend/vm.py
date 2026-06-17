import asyncio
import tempfile
from pathlib import Path

from .language_config import LANGUAGE_CONFIG
from .model import SubmissionStatus

COMPILE_TIMEOUT_SECONDS = 10
RUN_TIMEOUT_SECONDS = 5


async def compile_code(temp_dir: str, command: list[str]) -> dict:
    # Compile in the temp directory so generated binaries/classes stay isolated per submission.
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=temp_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=COMPILE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return {"success": False, "error": "compile timeout"}

    return {
        "success": process.returncode == 0,
        "output": stdout.decode(),
        "error": stderr.decode(),
    }


async def run_code(temp_dir: str, command: list[str], input_data: str) -> dict:
    # Feed testcase input over stdin and capture stdout for exact output comparison.
    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=temp_dir,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(input_data.encode()),
            timeout=RUN_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return {"status": SubmissionStatus.TLE, "output": "", "error": "time limit exceeded"}

    if process.returncode != 0:
        return {
            "status": SubmissionStatus.RUNTIME_ERROR,
            "output": stdout.decode(),
            "error": stderr.decode(),
        }

    return {
        "status": SubmissionStatus.ACCEPTED,
        "output": stdout.decode(),
        "error": stderr.decode(),
    }

async def mini_machine(submission, test_cases):
    config = LANGUAGE_CONFIG[submission.language]

    with tempfile.TemporaryDirectory() as temp_dir:
        source_file = Path(temp_dir) / config["filename"]

        with open(source_file, "w") as f:
            f.write(submission.code)

        # compile if needed
        if config["compile"]:
            compile_result = await compile_code(
                temp_dir,
                config["compile"]
            )

            if not compile_result["success"]:
                return {
                    "status": SubmissionStatus.COMPILE_ERROR
                }

        # run every testcase
        for testcase in test_cases:

            run_result = await run_code(
                temp_dir,
                config["run"],
                testcase.input_data
            )

            if run_result["status"] != SubmissionStatus.ACCEPTED:
                return {"status": run_result["status"]}

            actual = run_result["output"].strip()
            expected = testcase.output_data.strip()

            if actual != expected:
                return {"status": SubmissionStatus.WRONG_ANSWER}

        return {"status": SubmissionStatus.ACCEPTED}
