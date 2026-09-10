# Fly production delivery (#26)

The `CI` workflow is the only automatic entry point. On PRs it runs quality
checks only. On pushes to `main`, the reusable `fly-deploy.yml` is called with
`needs: [ci-gate]`. The normal GitHub success condition prevents the call when
the gate fails, is skipped, or is cancelled. Both caller and callee require a
`push` event on `refs/heads/main`. The reusable workflow has no independent push,
PR, or manual trigger and no user-supplied revision input.

Checkout explicitly selects `github.sha` and the shell verifies HEAD equals
`GITHUB_SHA`: tests and deployment refer to the same main commit. The image is
tagged with the commit SHA and receives the OCI revision label. A successful
deployment summary records the SHA, image tag and public smoke result. An image
tag identifies the build but is not an immutable digest; #28 covers immutable
release selection and rollback.

All actions are pinned to full commit SHAs; flyctl is pinned to `0.4.101` rather
than implicitly downloading latest. Permissions are `contents: read`. Checkout
does not persist credentials. The Fly token is available only to the deploy step
in the `Production` job, never to tests, checkout or public smoke. The caller does
not use `secrets: inherit`; Production supplies the environment secret.

## Concurrency and failure

PR runs cancel obsolete runs. Main runs do not cancel an in-progress deployment.
The CI concurrency group serializes main runs and the deploy job retains the
existing `deploy-group` with cancellation disabled. GitHub may replace queued
runs with a newer pending run; this does not bypass any checks or cancel a
running deploy. This is not a FIFO queue of every commit.

Deploy has a 20-minute timeout; public smoke has a 2-minute step timeout. If the
smoke fails, deployment is marked failed, but the release may already be live.
No automatic rollback is introduced. A maintainer must inspect the failed run
and app health before authorizing further production actions.

## Health checks and local validation

`fly.toml` defines a service check on `GET /health`, every 15 seconds, with a
5-second timeout and 10-second startup grace. These are initial conservative
values for the current lightweight FastAPI startup; tune with observed startup
and request times. `/test-ai` is never a health check.

The public smoke requires HTTP 200 and exactly `{"status":"healthy"}`. It rejects
redirects, retries failures up to six times with five-second waits and a
ten-second socket timeout, and exits nonzero on exhaustion. It does not print
response bodies, exception details, or credentials.

```bash
# Python 3.11 environment with requirements.txt installed (see ci-quality-gates.md)
python -m pytest tests/test_deploy_workflow.py tests/test_deploy_health.py
python -m pytest
actionlint
flyctl config validate --strict   # requires Fly authentication; no deployment
docker build --tag briskmail-ci:local .
bash scripts/ci/container-smoke.sh briskmail-ci:local
python3 scripts/ci/public_health.py https://email-classifier-api.fly.dev/health
```

The policy tests parse YAML/TOML and assert the intended security controls;
actionlint validates the workflow schema and expressions. The smoke tests mock
HTTP responses and fail under the suite's network guard if a real connection is
attempted. No application behavior or provider integration changes.

## Production activation — approval required

Before merging, obtain explicit owner approval immediately before each remote
configuration/credential change. Proposed settings:

1. Restrict `Production` deployments to the branch `main` (no tags).
2. Require approval by `Brunotlps` and disable administrator bypass. Allow
   self-review because the project has a solo maintainer; each production run
   still waits for that explicit approval.
3. Store a named, expiring `FLY_API_TOKEN` only in `Production`. The current
   repository-level secret cannot be retrieved from GitHub; it must be supplied
   by the owner or replaced. Do not try to extract it through workflow logs.
4. After an authorized successful deployment using the environment token,
   remove the redundant repository secret and revoke the identified superseded
   Fly token, with explicit approval for those exact targets.

These settings are proposals until the API confirms them. Merge, environment
approval, production deployment, credential creation and revocation require
separate explicit authorization within the agreed scope.

## Token scope and rotation

The local audit record for the 2026-06-10 incident (not tracked in Git) reported
that an app-scoped token failed at the classic remote builder and an org-scoped
token worked. That historical observation does not prove the restriction still
exists with flyctl 0.4.101. Official Fly guidance favors app-scoped deploy tokens;
the minimum currently functional scope must be tested, not assumed.

Keep `--remote-only --depot=false`: the historical remote builder authorization
issue and Depot/PyPI connectivity failures are documented in the incident and
`DECISIONS.md`. Changing builders would expand this issue unnecessarily.

After authorization and local `flyctl auth login`, the owner can create a named
app-scoped token with a finite lifetime (proposal: 90 days / `2160h`) and pass it
directly to GitHub via stdin, without displaying it or writing a plaintext file:

```bash
set -o pipefail
flyctl tokens create deploy --app email-classifier-api \
  --name briskmail-production-ci --expiry 2160h \
  | gh secret set FLY_API_TOKEN --env Production
```

The first authorized main deployment tests both remote build access and health.
If it fails on builder authorization, preserve the logs and obtain approval
before replacing it with an org-scoped token. Do not silently widen privileges.
Record the tested CLI version, failure stage, exact organization, token ID/name,
expiry and successful replacement run as an exception in the PR/runbook (never
the token value). The exception must explain that other apps in that org are
reachable and assign owner Bruno Teixeira Lopes to reassess it on rotation or a
builder/CLI change. Until that trial, scope validation remains pending.

Rotate before expiry (review by day 60): inventory token IDs, create replacement
with the narrowest verified scope, update the Production secret via stdin,
authorize a deployment, verify Fly checks and public health, then revoke only
the superseded token ID after explicit approval. A failed replacement does not
authorize revocation of the working credential. Never use an unbounded lifetime
or `fly auth token` as the persistent CI secret.

## Acceptance record

Baseline: `af3fe56`, 54 Python tests passed; direct push deploy, no Fly service
check, Production unprotected with no environment secret. Local Fly session was
not authenticated. Red: three parsed-policy tests failed on the missing gate,
independent push trigger and missing health check; smoke module was absent.
Green: 11 focused tests and all 65 Python tests passed; actionlint passed. A real
temporary local HTTP server confirmed CLI exit 0 for healthy HTTP 200 and exit 1
for HTTP 200 with an error body. Docker build and isolated `/health` smoke passed.

[PR #30](https://github.com/Brunotlps/email-classifier/pull/30) remote evidence:

- [Initial green CI](https://github.com/Brunotlps/email-classifier/actions/runs/34398063559)
  at `d913e17`: Python, extension, container and ci-gate passed; deploy skipped.
- [Controlled failure](https://github.com/Brunotlps/email-classifier/actions/runs/34398245915)
  at `772b2fb`: an additional synthetic test failed, Python/ci-gate failed and
  deploy stayed skipped. The synthetic test was then removed; no application
  test was disabled. This is a PR-side exclusion check; main's gate dependency
  is also checked structurally and must be confirmed in the authorized main run.

Remote acceptance requires a green PR with deploy skipped, a controlled failing
CI with deploy skipped, approved Production settings/credentials, and an
authorized main run proving gate-before-deploy for the same SHA, healthy Fly
service checks and successful public smoke. Keep `Refs #26` while any remain
unverified; do not close the issue based solely on a green PR.

Sources: [GitHub reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows),
[Fly access tokens](https://fly.io/docs/security/tokens/),
[Fly service checks](https://fly.io/docs/reference/configuration/#http_servicechecks).
