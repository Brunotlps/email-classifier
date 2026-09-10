"""ATDD: controles contínuos de supply chain e análise estática da issue #27."""
from pathlib import Path
import re

import yaml


ROOT = Path(__file__).resolve().parents[1]
FULL_SHA_ACTION = re.compile(r"[^@]+@[0-9a-f]{40}")


def load_yaml(path: Path):
    # BaseLoader mantém a chave YAML "on" como string.
    return yaml.load(path.read_text(), Loader=yaml.BaseLoader)


def test_dependabot_updates_pip_and_github_actions_on_a_bounded_schedule():
    config = load_yaml(ROOT / ".github/dependabot.yml")
    assert config["version"] == "2"

    updates = {entry["package-ecosystem"]: entry for entry in config["updates"]}
    assert set(updates) == {"pip", "github-actions"}
    for entry in updates.values():
        assert entry["directory"] == "/"
        assert entry["schedule"]["interval"] == "weekly"
        assert entry["open-pull-requests-limit"] == "3"
        assert entry["groups"]["minor-and-patch"]["update-types"] == ["minor", "patch"]


def test_dependency_review_blocks_vulnerable_dependency_changes_on_pull_requests():
    workflow = load_yaml(ROOT / ".github/workflows/dependency-review.yml")
    assert set(workflow["on"]) == {"pull_request"}
    assert workflow["permissions"] == {"contents": "read"}

    job = workflow["jobs"]["dependency-review"]
    assert job["timeout-minutes"] == "5"
    step, = job["steps"]
    assert FULL_SHA_ACTION.fullmatch(step["uses"])
    assert step["with"] == {"fail-on-severity": "high"}


def test_codeql_scans_python_and_javascript_with_minimum_permissions():
    workflow = load_yaml(ROOT / ".github/workflows/codeql.yml")
    assert set(workflow["on"]) == {"push", "pull_request", "schedule"}
    assert workflow["on"]["push"]["branches"] == ["main"]
    assert workflow["on"]["pull_request"]["branches"] == ["main"]
    assert workflow["permissions"] == {"contents": "read"}

    job = workflow["jobs"]["analyze"]
    assert job["timeout-minutes"] == "10"
    assert job["permissions"] == {"contents": "read", "security-events": "write"}
    assert job["strategy"]["matrix"]["language"] == ["python", "javascript-typescript"]
    for step in job["steps"]:
        if "uses" in step:
            assert FULL_SHA_ACTION.fullmatch(step["uses"])


def test_triage_policy_covers_alerts_major_updates_false_positives_and_dependency_split():
    policy = (ROOT / "docs/security-supply-chain.md").read_text()
    for heading in (
        "## Triagem de alertas",
        "## Atualizações do Dependabot",
        "## Falsos positivos e exceções",
        "## Separação futura de dependências",
    ):
        assert heading in policy
