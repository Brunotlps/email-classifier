"""ATDD: políticas explícitas do grafo de entrega, sobre YAML/TOML parseados."""
from pathlib import Path
import re
import tomllib

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
    assert deploy["uses"] == "./.github/workflows/fly-deploy.yml"
    assert "secrets" not in deploy
    assert ci["concurrency"]["cancel-in-progress"] == "${{ github.event_name == 'pull_request' }}"


def test_reusable_deploy_has_no_independent_trigger_or_untrusted_ref():
    deploy_workflow = workflow("fly-deploy.yml")
    assert set(deploy_workflow["on"]) == {"workflow_call"}
    assert deploy_workflow["permissions"] == {"contents": "read"}
    job = deploy_workflow["jobs"]["deploy"]
    assert job["if"] == MAIN_PUSH
    assert job["environment"]["name"] == "Production"
    assert job["concurrency"] == {"group": "deploy-group", "cancel-in-progress": "false"}
    assert 0 < int(job["timeout-minutes"]) <= 20
    checkout = job["steps"][0]
    assert checkout["with"]["ref"] == "${{ github.sha }}"
    assert checkout["with"]["persist-credentials"] == "false"
    for step in job["steps"]:
        if "uses" in step:
            assert re.fullmatch(r"[^@]+@[0-9a-f]{40}", step["uses"])


def test_fly_service_checks_health_without_ai():
    config = tomllib.loads((ROOT / "fly.toml").read_text())
    check, = config["http_service"]["checks"]
    assert check == {
        "method": "GET", "path": "/health", "interval": "15s",
        "timeout": "5s", "grace_period": "10s",
    }
