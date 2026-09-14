"""Build the only image reference accepted by the production rollback workflow."""

import re
import sys


IMAGE_REPOSITORY = "registry.fly.io/email-classifier-api"
COMMIT_SHA = re.compile(r"[0-9a-f]{40}")


def image_for_sha(commit_sha: str) -> str:
    """Return the Fly image tag for a validated commit reference."""
    if not isinstance(commit_sha, str) or COMMIT_SHA.fullmatch(commit_sha) is None:
        raise ValueError("rollback reference must be a lowercase 40-character commit SHA")
    return f"{IMAGE_REPOSITORY}:{commit_sha}"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: rollback_image.py COMMIT_SHA")
    try:
        print(image_for_sha(sys.argv[1]))
    except ValueError as error:
        raise SystemExit(str(error)) from error
