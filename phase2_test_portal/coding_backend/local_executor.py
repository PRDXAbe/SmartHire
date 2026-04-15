"""Local code execution engine using Python subprocess (no API key needed)."""
import os
import subprocess
import sys
import tempfile
import base64


class LocalCodeExecutor:
    """Execute code locally using subprocess. For demo/prototype use only."""

    # Supported languages (expand as needed)
    LANGUAGE_CONFIG = {
        "python": {
            "cmd": ["python", "-u"],
            "extension": ".py"
        },
        "javascript": {
            "cmd": ["node"],
            "extension": ".js"
        }
    }

    def __init__(self, time_limit: float = 5.0, memory_limit_kb: int = 128000):
        self.time_limit = time_limit
        self.memory_limit = memory_limit_kb

    def execute(
        self,
        source_code: str,
        language: str = "python",
        stdin: str = "",
        expected_output: str = None
    ) -> dict:
        """
        Execute code and return results.

        Args:
            source_code: Code to run
            language: Programming language
            stdin: Standard input
            expected_output: Expected output for validation

        Returns:
            {
                "stdout": str,
                "stderr": str,
                "status": str,
                "time": float,
                "memory": int
            }
        """
        if language not in self.LANGUAGE_CONFIG:
            return {
                "stdout": "",
                "stderr": f"Language '{language}' not supported. Use: {list(self.LANGUAGE_CONFIG.keys())}",
                "status": "Error",
                "time": 0,
                "memory": 0
            }

        config = self.LANGUAGE_CONFIG[language]
        status = "Accepted"

        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=config["extension"],
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(source_code)
            temp_path = f.name

        try:
            # Execute code
            start_time = os.times()[2]  # System time

            result = subprocess.run(
                config["cmd"] + [temp_path],
                input=stdin,
                capture_output=True,
                text=True,
                timeout=self.time_limit,
                cwd=os.path.dirname(temp_path)
            )

            end_time = os.times()[2]
            execution_time = round(end_time - start_time, 3)

            stdout = result.stdout
            stderr = result.stderr

            if result.returncode != 0:
                status = "Runtime Error" if stderr else "Wrong Answer"
            elif expected_output and stdout.strip() != expected_output.strip():
                status = "Wrong Answer"

        except subprocess.TimeoutExpired:
            stdout = ""
            stderr = f"Time Limit Exceeded (>{self.time_limit}s)"
            status = "Time Limit Exceeded"
            execution_time = self.time_limit
        except Exception as e:
            stdout = ""
            stderr = str(e)
            status = "Error"
            execution_time = 0

        finally:
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)

        return {
            "stdout": stdout,
            "stderr": stderr,
            "status": status,
            "time": execution_time,
            "memory": 0  # Memory tracking not available on Windows
        }

    def run_test_cases(
        self,
        source_code: str,
        test_cases: list,
        language: str = "python"
    ) -> dict:
        """
        Run code against multiple test cases.

        Args:
            source_code: Candidate's solution
            test_cases: List of {"input": str, "expected_output": str}
            language: Programming language

        Returns:
            {
                "total": int,
                "passed": int,
                "failed": int,
                "percentage": float,
                "results": [...]
            }
        """
        results = []
        passed_count = 0
        total = len(test_cases)

        for i, tc in enumerate(test_cases):
            result = self.execute(
                source_code=source_code,
                language=language,
                stdin=tc["input"],
                expected_output=tc["expected_output"]
            )

            test_passed = (result["status"] == "Accepted" and
                          result["stdout"].strip() == tc["expected_output"].strip())

            if test_passed:
                passed_count += 1

            results.append({
                "test_case": i + 1,
                "passed": test_passed,
                "stdout": result["stdout"].strip(),
                "expected": tc["expected_output"].strip(),
                "status": result["status"],
                "time": result["time"],
                "memory": result["memory"]
            })

        return {
            "total": total,
            "passed": passed_count,
            "failed": total - passed_count,
            "percentage": round((passed_count / total) * 100, 2) if total > 0 else 0,
            "results": results
        }

    def quick_execute(
        self,
        source_code: str,
        language: str = "python",
        stdin: str = ""
    ) -> dict:
        """Quickly execute code and return output."""
        return self.execute(source_code, language, stdin)
