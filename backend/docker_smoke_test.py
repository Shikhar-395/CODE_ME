import asyncio
from types import SimpleNamespace

from .docker_executor import check_docker_image, execute_in_docker
from .model import SubmissionStatus


async def main() -> None:
    await check_docker_image()

    test_cases = [
        SimpleNamespace(input_data="20 22\n", output_data="42\n"),
        SimpleNamespace(input_data="-5 8\n", output_data="3\n"),
    ]
    submissions = [
        SimpleNamespace(
            id=1,
            language="python",
            code=(
                "a, b = map(int, input().split())\n"
                "print(a + b)\n"
            ),
        ),
        SimpleNamespace(
            id=2,
            language="cpp",
            code=(
                "#include <iostream>\n"
                "int main() { long long a, b; std::cin >> a >> b; "
                "std::cout << a + b << '\\n'; }\n"
            ),
        ),
        SimpleNamespace(
            id=3,
            language="java",
            code=(
                "import java.util.Scanner;\n"
                "public class Main {\n"
                "  public static void main(String[] args) {\n"
                "    Scanner scanner = new Scanner(System.in);\n"
                "    long a = scanner.nextLong();\n"
                "    long b = scanner.nextLong();\n"
                "    System.out.println(a + b);\n"
                "  }\n"
                "}\n"
            ),
        ),
        SimpleNamespace(
            id=4,
            language="javascript",
            code=(
                "const [a, b] = require('fs').readFileSync(0, 'utf8')\n"
                "  .trim().split(/\\s+/).map(Number);\n"
                "console.log(a + b);\n"
            ),
        ),
    ]

    for submission in submissions:
        result = await execute_in_docker(submission, test_cases)
        if result["status"] != SubmissionStatus.ACCEPTED:
            raise SystemExit(
                f"Docker {submission.language} smoke test failed: {result}"
            )
        print(f"Docker {submission.language} smoke test passed.")


if __name__ == "__main__":
    asyncio.run(main())
