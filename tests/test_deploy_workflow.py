"""ATDD: políticas explícitas do grafo de entrega, sobre YAML/TOML parseados."""
from pathlib import Path
import re
import tomllib

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
MAIN_PUSH = "${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}"


def workflow(name):
    # BaseLoader preserva a chave YAML 'on' como string.
    return yaml.load((ROOT / ".github/workflows" / name).read_text(), Loader=yaml.BaseLoader)


def test_deploy_requires_gate_in_the_same_run_and_main_push():
    ci = workflow("ci.yml")
    deploy = ci["jobs"]["deploy"]
    assert deploy["needs"] == ["ci-gate"]
    assert deploy["if"] == MAIN_PUSH
    assert deploy["environment"]["name"] == "Production"
    assert deploy["permissions"] == {"contents": "read"}
    assert ci["concurrency"]["cancel-in-progress"] == "${{ github.event_name == 'pull_request' }}"


def test_main_pushes_use_independent_ci_concurrency_groups():
    ci = workflow("ci.yml")

    assert ci["concurrency"]["group"] == (
        "ci-${{ github.workflow }}-"
        "${{ github.event_name == 'pull_request' && github.ref || github.run_id }}"
    )
    assert ci["concurrency"]["cancel-in-progress"] == (
        "${{ github.event_name == 'pull_request' }}"
    )


def test_legacy_deploy_pointer_cannot_deploy():
    deploy_workflow = workflow("fly-deploy.yml")
    assert set(deploy_workflow["on"]) == {"workflow_dispatch"}
    assert deploy_workflow["permissions"] == {}
    assert "never-deploy" in deploy_workflow["jobs"]["disabled"]["if"]


def test_ci_deploy_has_immutable_actions_and_exact_commit():
    deploy = workflow("ci.yml")["jobs"]["deploy"]
    assert deploy["concurrency"] == {"group": "deploy-group", "cancel-in-progress": "false"}
    assert deploy["steps"][0]["with"]["ref"] == "${{ github.sha }}"
    for step in deploy["steps"]:
        if "uses" in step:
            assert re.fullmatch(r"[^@]+@[0-9a-f]{40}", step["uses"])


def test_fly_service_checks_health_without_ai():
    config = tomllib.loads((ROOT / "fly.toml").read_text())
    check, = config["http_service"]["checks"]
    assert check == {
        "method": "GET", "path": "/health", "interval": "15s",
        "timeout": "5s", "grace_period": "10s",
    }


def test_manual_rollback_is_protected_and_uses_an_immutable_image():
    rollback = workflow("fly-rollback.yml")
    inputs = rollback["on"]["workflow_dispatch"]["inputs"]
    job = rollback["jobs"]["rollback"]

    assert rollback["permissions"] == {"contents": "read"}
    assert inputs["commit_sha"]["required"] == "true"
    assert inputs["confirmation"]["required"] == "true"
    assert inputs["confirmation"]["type"] == "choice"
    assert job["environment"]["name"] == "Production"
    assert job["permissions"] == {"contents": "read"}
    assert job["concurrency"] == {"group": "production-deploy", "cancel-in-progress": "false"}
    assert all(
        re.fullmatch(r"[^@]+@[0-9a-f]{40}", step["uses"])
        for step in job["steps"]
        if "uses" in step
    )

    runs = [step["run"] for step in job["steps"] if "run" in step]
    assert any("scripts/ci/rollback_image.py" in command for command in runs)
    assert any("flyctl releases --app email-classifier-api --image" in command for command in runs)
    assert any(
        'flyctl deploy --app email-classifier-api --image "$ROLLBACK_IMAGE"' in command
        for command in runs
    )
    assert all("${{ inputs." not in command for command in runs)
    deploy_step = next(step for step in job["steps"] if step.get("name") == "Deploy the selected existing image")
    assert deploy_step["env"] == {
        "FLY_API_TOKEN": "${{ secrets.FLY_API_TOKEN }}",
        "ROLLBACK_IMAGE": "${{ steps.target.outputs.image }}",
    }


def test_rollback_reference_validation_rejects_mutable_or_malformed_input():
    from scripts.ci.rollback_image import image_for_sha

    commit_sha = "a" * 40
    assert image_for_sha(commit_sha) == f"registry.fly.io/email-classifier-api:{commit_sha}"

    for invalid in ("latest", "main", "a" * 39, "a" * 40 + "x", "A" * 40):
        with pytest.raises(ValueError):
            image_for_sha(invalid)


def test_issue_28_delivery_policy_is_documented():
    document = (ROOT / "docs/fly-production-deploy.md").read_text().lower()

    for criterion in (
        "rollback runbook",
        "15-minute observation window",
        "direct deploy",
        "staging",
        "canary",
        "ci-gate",
        "path filters",
        "vercel preview",
        "rollback executor",
    ):
        assert criterion in document
