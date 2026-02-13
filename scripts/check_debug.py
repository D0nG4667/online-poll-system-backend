import os
import sys


def main() -> int:
    file_path = os.path.join("config", "settings", "production.py")
    if not os.path.exists(file_path):
        # If file doesn't exist, we can't check it.
        # But failing might be safer if it SHOULD exist.
        # For now, pass.
        return 0

    with open(file_path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            # Check for DEBUG=True (naive check, sufficient for settings)
            if "DEBUG" in line and "True" in line and not line.strip().startswith("#"):
                # Better check:
                # Remove spaces
                normalized = line.replace(" ", "")
                if "DEBUG=True" in normalized:
                    print(f"Error: DEBUG = True found in {file_path}:{i}")  # noqa: T201
                    return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
