# Publishing `syntri-sdk` to PyPI

The PyPI publish is automated by `.github/workflows/publish-pypi.yml`. It runs
on any pushed tag matching `python/v*`, builds the sdist and wheel, and uploads
them to PyPI using **trusted publishing (OIDC)** — no API token is stored. The
language prefix keeps TypeScript/Go tags from triggering a PyPI publish.

This is the same trusted-publishing pattern used by `syntri-contracts`. The
GitHub environment is named `pypi-sdk` to keep it separate from the TypeScript
npm environment.

## One-time setup

Trusted publishing links a PyPI project to a specific GitHub repo + workflow +
environment, so no secret is ever stored. All three steps must be done before
the first release tag.

1. **Create the `syntri-sdk` project on PyPI.** Sign in at
   <https://pypi.org/>. The package name is `syntri-sdk` — confirm it is
   available or that you own it. (It is distinct from `syntri-contracts`.)

2. **Add the trusted publisher.** On the project's
   **Settings → Publishing → Add a new pending publisher** (or, once the
   project exists, **Manage → Publishing**), add a GitHub publisher with:

   - **Owner / repository:** `DomaniLabs/syntri-sdk`
   - **Workflow name:** `publish-pypi.yml`
   - **Environment:** `pypi-sdk`

3. **Create the `pypi-sdk` environment on GitHub.** In the
   `DomaniLabs/syntri-sdk` repo: **Settings → Environments → New environment**,
   name it `pypi-sdk`. (Optionally add protection rules — required reviewers,
   or restrict to the `main` branch / `python/v*` tags.)

## Cutting a release

1. Bump `version` in `python/pyproject.toml` (e.g. `0.1.0` → `0.1.1`).
2. Commit the bump on `main`.
3. Tag and push, matching the version:

   ```bash
   git tag python/v0.1.0
   git push origin --tags
   ```

The `Publish Python SDK to PyPI` workflow runs `python -m build`, then
`pypa/gh-action-pypi-publish`. Watch it under the repo's **Actions** tab. On
success the new version is live on PyPI.

## Notes

- The tag version and `pyproject.toml` version should match. PyPI refuses to
  republish a version that already exists.
- CI (`ci.yml`) already runs ruff, mypy, and pytest across Python 3.10/3.11/3.12
  on every push and PR, so a tag should only be cut from a green `main`.
- To do a dry run locally: `python -m build` then `twine check dist/*`.
