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
    assert deploy["environment"]["name"] == "Production"
    assert deploy["permissions"] == {"contents": "read"}
    assert ci["concurrency"]["cancel-in-progress"] == "${{ github.event_name == 'pull_request' }}"


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
