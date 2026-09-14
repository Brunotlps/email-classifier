# Multipart upload security (#40)

`python-multipart` moves from 0.0.12 to 0.0.31, the minimum version covering
the eight alerts recorded in #40. FastAPI 0.115.0 and Starlette 0.38.6 remain
unchanged. The existing Dependabot PR #36 carries the dependency update;
regression tests exercise the real `/api/v1/classify-file` parser with the AI
analysis mocked and external networking blocked.

## Verified behavior

- Plain `filename` controls extension validation even when `filename*`
  supplies a conflicting extension. An unsupported plain filename is rejected
  before AI analysis; a supported plain filename retains normal upload behavior.
- Excessive multipart headers (count or length) and an oversized boundary return
  HTTP 400 before AI analysis. Test payloads are bounded to a few kilobytes;
  they verify rejection, not throughput or an exhaustive denial-of-service test.
- Missing boundary returns HTTP 400. Valid TXT, EML and PDF uploads still work;
  EML/PDF extraction reaches the mocked analyzer with the expected content.
- Existing empty-file, over-5MB and unsupported-extension checks remain covered.

Upstream now defaults to eight headers per part, 4224 bytes per header and a
256-byte boundary limit. Clients exceeding those limits receive HTTP 400.
The browser's ordinary file-upload path does not require custom oversized
metadata. Requests using only extended filename parameters may also change
behavior; the application continues to rely on standard `filename`.

## Red and Green evidence

Baseline on Python 3.11.15 with python-multipart 0.0.12: 70 tests passed.
The five new security regression cases failed against 0.0.12: filename
precedence differed, and all three excessive-metadata cases returned HTTP 200.
The additional EML/missing-boundary checks already passed and are compatibility
coverage, not evidence of a newly fixed behavior.

With only python-multipart changed to 0.0.31, the 14 upload tests and full
78-test suite passed. `pip check` found no broken requirements. Warnings from
legacy dependency/import APIs remain visible, including the `multipart`
compatibility import used by the current framework. PDF parser modernization
is tracked separately in #38.

Remote closure requires green PR checks and integration, followed by confirming
the eight python-multipart alerts are fixed. A green PR or closed alert does not
prove production is updated: production deployment still requires authorization,
a successful CI for the deployed SHA and the `/health` smoke. Existing queued
production approvals must be resolved before this correction can be delivered.

Sources: [upstream release 0.0.31](https://github.com/Kludex/python-multipart/releases/tag/0.0.31),
[header limits](https://github.com/Kludex/python-multipart/pull/267),
[filename parameter handling](https://github.com/Kludex/python-multipart/pull/291).
