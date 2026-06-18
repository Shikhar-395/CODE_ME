#!/usr/bin/env python3
import json
import os
import resource
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


MAX_REQUEST_BYTES = 8 * 1024 * 1024
MAX_RESPONSE_BYTES = 1024 * 1024

LANGUAGE_CONFIG = {
    "cpp": {
        "filename": "main.cpp",
        "compile": ["g++", "main.cpp", "-O2", "-pipe", "-o", "main"],
        "run": ["./main"],
    },
    "python": {
        "filename": "main.py",
        "compile": None,
        "run": ["python3", "-I", "main.py"],
    },
    "java": {
        "filename": "Main.java",
        "compile": ["javac", "Main.java"],
        "run": [
            "java",
            "-Xms16m",
            "-Xmx256m",
            "-XX:MaxMetaspaceSize=96m",
            "Main",
        ],
    },
    "javascript": {
        "filename": "main.js",
        "compile": None,
        "run": ["node", "--max-old-space-size=256", "main.js"],
    },
}


def judge(payload: dict[str, Any]) -> dict[str, str]:
    language = payload.get("language")
    config = LANGUAGE_CONFIG.get(language)
    if config is None:
        return _result("runtime_error", error=f"Unsupported language: {language}")

    code = payload.get("code")
    test_cases = payload.get("test_cases")
    if not isinstance(code, str) or not isinstance(test_cases, list):
        return _result("runtime_error", error="Invalid judge payload")

    limits = payload.get("limits") or {}
    compile_timeout = _bounded_number(
        limits.get("compile_timeout_seconds"),
        default=10.0,
        minimum=0.1,
        maximum=30.0,
    )
    run_timeout = _bounded_number(
        limits.get("run_timeout_seconds"),
        default=5.0,
        minimum=0.1,
        maximum=15.0,
    )
    output_bytes = int(
        _bounded_number(
            limits.get("output_bytes"),
            default=1024 * 1024,
            minimum=1024,
            maximum=4 * 1024 * 1024,
        )
    )

    with tempfile.TemporaryDirectory(prefix="judge-", dir="/tmp") as temp_dir:
        workdir = Path(temp_dir)
        source_path = workdir / config["filename"]
        source_path.write_text(code, encoding="utf-8")

        if config["compile"]:
            compiled = _run_process(
                config["compile"],
                cwd=workdir,
                input_data=b"",
                timeout_seconds=compile_timeout,
                output_bytes=output_bytes,
            )
            if compiled["timed_out"]:
                return _result("compile_error", error="Compilation timed out")
            if compiled["returncode"] != 0:
                return _result(
                    "compile_error",
                    error=compiled["stderr"] or compiled["stdout"],
                )

        for testcase in test_cases:
            if not isinstance(testcase, dict):
                return _result("runtime_error", error="Invalid test case")

            input_data = str(testcase.get("input", "")).encode()
            expected = str(testcase.get("expected_output", "")).strip()
            executed = _run_process(
                config["run"],
                cwd=workdir,
                input_data=input_data,
                timeout_seconds=run_timeout,
                output_bytes=output_bytes,
            )

            if executed["timed_out"]:
                return _result("tle", error="Time limit exceeded")
            if executed["returncode"] != 0:
                return _result(
                    "runtime_error",
                    output=executed["stdout"],
                    error=executed["stderr"],
                )
            if executed["stdout"].strip() != expected:
                return _result("wrong_answer")

    return _result("accepted")


def _run_process(
    command: list[str],
    cwd: Path,
    input_data: bytes,
    timeout_seconds: float,
    output_bytes: int,
) -> dict[str, Any]:
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=stdout_file,
            stderr=stderr_file,
            start_new_session=True,
            preexec_fn=lambda: _apply_child_limits(timeout_seconds, output_bytes),
        )

        timed_out = False
        try:
            process.communicate(input=input_data, timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()

        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read(output_bytes).decode(errors="replace")
        stderr = stderr_file.read(output_bytes).decode(errors="replace")

    return {
        "returncode": process.returncode,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
    }


def _apply_child_limits(timeout_seconds: float, output_bytes: int) -> None:
    cpu_seconds = max(1, int(timeout_seconds) + 1)
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
    resource.setrlimit(resource.RLIMIT_FSIZE, (output_bytes, output_bytes))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_NPROC, (128, 128))


def _bounded_number(
    value: Any,
    *,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return min(max(parsed, minimum), maximum)


def _result(
    status: str,
    *,
    output: str = "",
    error: str = "",
) -> dict[str, str]:
    return {
        "status": status,
        "output": output[: MAX_RESPONSE_BYTES // 2],
        "error": error[: MAX_RESPONSE_BYTES // 2],
    }


def main() -> None:
    request = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
    if len(request) > MAX_REQUEST_BYTES:
        response = _result(
            "runtime_error",
            error=f"Request exceeds {MAX_REQUEST_BYTES} bytes",
        )
    else:
        try:
            payload = json.loads(request)
            if not isinstance(payload, dict):
                raise ValueError("Request must be a JSON object")
            response = judge(payload)
        except Exception as exc:
            response = _result(
                "runtime_error",
                error=f"Judge agent error: {exc}",
            )

    encoded = json.dumps(response, separators=(",", ":")).encode()
    if len(encoded) > MAX_RESPONSE_BYTES:
        encoded = json.dumps(
            _result("runtime_error", error="Judge response exceeded its limit"),
            separators=(",", ":"),
        ).encode()
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    main()
