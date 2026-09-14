# Fly production delivery (#26, #28)

The `CI` workflow is the only automatic entry point. On PRs it runs quality
checks only. On pushes to `main`, the direct `deploy` job in `ci.yml` has
`needs: [ci-gate]`. The normal GitHub success condition prevents the job when
the gate fails, is skipped, or is cancelled. Both caller and callee require a
`push` event on `refs/heads/main`. The old `fly-deploy.yml` is a disabled operator
pointer and cannot deploy; there is no independent deploy trigger or user-supplied
revision input.

Checkout explicitly selects `github.sha` and the shell verifies HEAD equals
`GITHUB_SHA`: tests and deployment refer to the same main commit. The image is
tagged with the commit SHA and receives the OCI revision label. A successful
deployment summary records the SHA, image tag and public smoke result. #28 adds
validated selection and redeployment of a previously successful SHA-tagged
release without rebuilding source.

## Rollback runbook (#28)

Fly rollback means redeploying an image from a previously successful release. The
rollback target is selected by its lowercase 40-character commit SHA, which is
the tag written by the production deploy job. The workflow accepts no branch,
`latest`, or free-form image value. It derives
`registry.fly.io/email-classifier-api:$SHA`, requires the exact confirmation
choice, runs only when dispatched from `main`, and requests the `Production`
environment. The environment approval remains the final remote authorization.

The rollback executor is the maintainer who dispatches **Fly Rollback** and
approves `Production`. The validator is the same maintainer during the incident,
using the release list and health checks below; a second maintainer can perform
the validation when available. The workflow has `contents: read`, exposes the
Fly token only to the deploy step, and never changes Fly secrets or application
configuration through a separate command.

1. Record the incident time, observed signal, current release, and the last
   known-good release. Inspect the current app without changing it:

   ```bash
   fly status --app email-classifier-api
   fly releases --app email-classifier-api --image
   ```

2. Select a previously successful commit SHA from the release list. Confirm that
   its image is still present and that the current Fly secrets and configuration
   do not need a separate, explicitly reviewed change. Fly rollback changes the
   VM image; it does not restore old secrets, `fly.toml` values, or database
   state.

3. In GitHub Actions, choose **Fly Rollback**, select `main`, enter the selected
   SHA in `commit_sha`, and choose
   `I_UNDERSTAND_PRODUCTION_ROLLBACK`. Approve the `Production` environment only
   after checking those values. The workflow runs:

   ```bash
   flyctl deploy --app email-classifier-api \
     --image registry.fly.io/email-classifier-api:$SHA \
     --strategy rolling
   ```

   This reuses the existing image and does not build source. The normal source
   deploy in `ci.yml` keeps `--remote-only --depot=false`; those flags are not
   removed or changed by the image-only rollback path.

4. Verify the Fly release and service checks, then run the public probe:

   ```bash
   fly status --app email-classifier-api
   python3 scripts/ci/public_health.py \
     https://email-classifier-api.fly.dev/health
   ```

5. Observe production for 15 minutes after the rollback. The release is
   considered stable when Fly checks remain healthy, `/health` continues to
   return the expected JSON, and logs, restarts, error rate, and request
   latency return to the normal baseline. The executor records the target and
   timestamps in the incident/PR. A single signal does not trigger an
   automatic rollback; the maintainer decides whether to hold, roll forward,
   or repeat the runbook.

The rollback procedure is rehearsed locally and without credentials by testing
the reference validator:

```bash
python3 scripts/ci/rollback_image.py \
  aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

It prints the exact registry reference. Mutable values such as `latest`, branch
names, uppercase strings, and malformed SHAs fail before any Fly command. This
rehearsal does not call Fly or alter production.

## Delivery strategy and deferred scope

The project uses a direct deploy to production with three controls: the parallel
Python, extension, and container checks; the `ci-gate` job requiring all three
to succeed on the same commit; and manual `Production` approval. A separate
staging app or canary is deferred because this repository has one Fly app, no
staging configuration or secret set, and no traffic split mechanism. The
15-minute observation window above is the progressive control that fits the
current topology without inventing a second environment. No automatic rollback
is tied to one health signal.

There are no path filters today. This preserves `ci-gate` as the required
fallback for documentation, backend, extension, and container changes while a
baseline is collected. A future filter change must measure current job coverage
first, keep a safe fallback, and update the gate tests in a separate linked
follow-up; it is outside this rollback change.

Vercel previews remain enabled for the frontend integration. This PR does not
change preview creation or introduce a repository-side Vercel workflow. Any
reduction should follow a measured baseline and a separate linked follow-up so
frontend validation is not silently removed.

All actions are pinned to full commit SHAs; flyctl is pinned to `0.4.101` rather
than implicitly downloading latest. Permissions are `contents: read`. Checkout
does not persist credentials. The Fly token is available only to the deploy step
in the direct `Production` job, never to tests, checkout or public smoke. This
placement is deliberate: the first merge attempt showed an environment secret
was empty inside a called reusable workflow, so no Fly API call was made with it.

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
token worked. The authorized 2026-09-10 production run reproduced that behavior
with flyctl 0.4.101: the app-scoped token passed config validation but failed with
`Failed to start remote builder heartbeat: unauthorized`. An org-scoped token
with the same finite lifetime then completed the remote build and deployment.
Official Fly guidance favors app-scoped deploy tokens; this project records the
org-scoped token as a necessary exception for the retained remote-builder path.

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

The authorized trial used the `personal` organization, token name
`briskmail-production-ci`, and expiry `2026-12-08T20:18:33Z`. The replacement
run was [34475535289](https://github.com/Brunotlps/email-classifier/actions/runs/34475535289)
for SHA `a5de11c48ab81e0c34e1cddacda7c8f2dbf09a15`; it passed the remote build,
Fly service checks, and public `/health` smoke test. The exception must be
reassessed by Bruno Teixeira Lopes at rotation time or after a builder/CLI
change. Never record the token value.

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

The first authorized main run reached the deploy job after ci-gate passed, but
failed immediately because the environment secret was empty inside the reusable
workflow. No Fly API call or production change occurred. The implementation now
places deployment directly in `ci.yml` so the environment secret is resolved by
the same job that requests approval.

Remote acceptance requires a green PR with deploy skipped, a controlled failing
CI with deploy skipped, approved Production settings/credentials, and an
authorized main run proving gate-before-deploy for the same SHA, healthy Fly
service checks and successful public smoke. Keep `Refs #26` while any remain
unverified; all remote acceptance items are now evidenced by the merged PRs and
run `34475535289`.

Sources: [GitHub reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows),
[Fly access tokens](https://fly.io/docs/security/tokens/),
[Fly service checks](https://fly.io/docs/reference/configuration/#http_servicechecks).
