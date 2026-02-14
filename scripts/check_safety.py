# ruff: noqa: S603
import shutil
import subprocess
import sys


def main() -> int:
    # Running: uv pip list --format=freeze | safety check --stdin
    # But safer to just use safety with uv export via subprocess

    try:
        # Generate requirements list
        # We assume 'uv' is in PATH.
        # safety check --stdin expects installed packages format or requirements.txt

        # 1. Get frozen env
        uv_path = shutil.which("uv")
        if not uv_path:
            sys.stderr.write("Error: 'uv' command not found. Please verify uv is installed.\n")
            return 1

        freeze_proc = subprocess.run(
            [uv_path, "pip", "list", "--format=freeze"],
            capture_output=True,
            text=True,
            check=True,
        )
        requirements = freeze_proc.stdout

        # 2. Upgrade safety? No, assume it's installed in the tool env?
        # The hook uses 'system', so it uses the user's environment.
        # We need to make sure 'safety' is installed or run it via uv tool?

        safety_proc = subprocess.run(
            [uv_path, "run", "safety", "check", "--stdin"],
            input=requirements,
            text=True,
            capture_output=True,
            check=False,
        )

        sys.stdout.write(safety_proc.stdout)
        sys.stderr.write(safety_proc.stderr)

        if safety_proc.returncode != 0:
            return safety_proc.returncode

        return 0

    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error running uv: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
