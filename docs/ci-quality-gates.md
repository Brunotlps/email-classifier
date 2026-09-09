# CI quality gates (#25)

`CI` runs on every pull request targeting `main` and every push to `main`, including
documentation-only changes. There are no path filters. Python, extension and
container jobs run in parallel; `ci-gate` uses `always()` and accepts only `success`
from **all three** jobs. Failure, cancellation, or skipping any dependency must
produce a failing gate (an entirely cancelled run must never satisfy protection).

The workflow has `contents: read`, disables persisted checkout credentials, uses
full commit SHAs with release comments, and never references production secrets.
The aggregator needs no token permissions. Concurrency cancels obsolete runs for
the same workflow/ref. Timeouts are 10 minutes for Python, 5 for the extension,
15 for the container, and 2 for the aggregator. Expected PR duration is under
10 minutes; runner queues and cold dependency/image downloads can vary.

## Local commands

From the repository root, with Python 3.11, Node 24, and Docker available:

```bash
python3.11 -m venv /tmp/briskmail-quality-venv
source /tmp/briskmail-quality-venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest

node --test tests/extension_background.test.js
bash -e -o pipefail -c '
while IFS= read -r -d "" file; do
  node --check "$file"
done < <(find extension -type f -name "*.js" -print0)
'
node -e "JSON.parse(require('node:fs').readFileSync('extension/manifest.json', 'utf8'))"

docker build --tag briskmail-ci:local .
bash scripts/ci/container-smoke.sh briskmail-ci:local
git diff --check
```

No npm project, lint baseline, or type-checking configuration is introduced.
The smoke script creates an ephemeral container with `--network none`, no host
ports or volumes, and no credentials. It polls `/health` from inside the container,
requiring HTTP 200 and the exact JSON `{"status":"healthy"}`. Failure prints the
test container's logs; the exit trap removes that container on success or failure.
The local image is retained. Never substitute `/test-ai`: its HTTP 200 response
can contain an error and it depends on a real model.

For workflow validation, install a pinned actionlint into an isolated directory
(requires Go compatible with its module):

```bash
GOBIN=/tmp/briskmail-quality-tools go install github.com/rhysd/actionlint/cmd/actionlint@v1.7.12
/tmp/briskmail-quality-tools/actionlint
```

`actionlint` parses YAML and checks workflow semantics/expressions; when available,
it also invokes ShellCheck. It is a local authoring check, not a fourth required
CI job. No global installation is necessary.

## Deterministic test boundary

Before application imports, `tests/conftest.py` selects Ollama with an unavailable
loopback URL, clears the OpenAI key, and selects the test environment. An autouse
fixture fails attempted IP connections or DNS resolution. Unix sockets used by
asyncio remain available; TestClient/ASGI requests stay in process. This guard
covers the Python socket APIs used by the current suite; it is not an OS firewall
for subprocesses or native libraries.

All existing tests run, including slow-marked tests if any are added. `/test-ai`
uses a mocked client for success and failure; no test is skipped to obtain green
CI. Future live integration tests need a separate opt-in harness outside the
required offline suite, with test credentials only.

## Acceptance evidence

Baseline at `fcd715494b89239132a45ebf2fdaf9fed29bd20f` (2026-09-09):

- No PR workflow, required check, branch protection, or repository ruleset.
- Python 3.11.15: 52 passed, 1 failed with Ollama unavailable. The existing
  `/test-ai` test expected a provider field even when the endpoint returned an
  error body. This was preexisting network coupling.
- Node 24.14.1: existing test file, JavaScript syntax, and manifest parsing passed.
- Existing Dockerfile built successfully; existing deploy workflow passed actionlint.

Red → Green:

- Applying the network guard first made `/test-ai` fail with
  `External network is disabled in tests; mock the AI/HTTP client`.
- Mocking its client retained success coverage and added error-body coverage.
  Focused health tests: 4 passed; full Python suite: 54 passed.
- The new workflow passes actionlint 1.7.12. Its actual aggregator shell was
  executed against all 64 combinations of success/failure/cancelled/skipped:
  only all-success exits zero.
- Docker smoke requires a real HTTP response from the built image while external
  networking is disabled. PR execution and a controlled failing revision provide
  the remote scheduler/gate evidence; link those runs in the PR.

Remote evidence in [PR #29](https://github.com/Brunotlps/email-classifier/pull/29):

- [Initial green run](https://github.com/Brunotlps/email-classifier/actions/runs/34347260665)
  at `7ae4678`: all four jobs succeeded in 49 seconds including scheduling.
- [Controlled failure](https://github.com/Brunotlps/email-classifier/actions/runs/34347838464)
  at `3d844a0`: an additional temporary test deliberately failed; Python and
  `ci-gate` failed while extension and container passed. That probe was then
  removed without removing or weakening any application test.
- The controlled revision initially received no CI run after push; reopening the
  PR triggered the failure run. Verify automatic synchronization on the restored
  revision before declaring remote acceptance complete.

## Protection activation and delivery boundary

After the first green PR run, obtain explicit owner approval immediately before
configuring `main` to require a pull request and the `ci-gate` check from GitHub
Actions, require the branch to be up to date, enforce the rules for administrators,
and disallow force pushes and deletion. A required review count of zero permits
the solo maintainer to integrate an agent-authored PR while still requiring a PR.
Do not claim this protection is active until the remote API verifies it.

Use `Refs #25` while remote acceptance remains pending; change to `Closes #25`
once all criteria are met. Merge needs separate explicit approval. The existing
Fly workflow still deploys automatically on pushes to `main`, independently of CI;
merge approval must account for that production deployment. #26 will gate deploys.

The Docker base tag and transitive Python dependencies remain mutable; this work
makes test execution independent of live AI, not a fully reproducible dependency
lock or image build. Dependency locking and production deployment hardening are
outside this change. Existing dependency deprecation warnings remain visible in
pytest's warning count.

References: [GitHub workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax),
[required check behavior](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks),
[actionlint usage](https://github.com/rhysd/actionlint/blob/v1.7.12/docs/usage.md).
