# Publishing `syntri` to npm

The npm publish is automated by `.github/workflows/publish-npm.yml`. It runs on
any pushed tag matching `typescript/v*`, builds the package, and runs
`npm publish` using the `NPM_TOKEN` repository secret. The language prefix keeps
future Python/Go tags from triggering an npm publish.

## One-time setup

1. **Create an npm account / org.** Sign in at <https://www.npmjs.com/>. The
   package name is `syntri` (unscoped) — confirm it is available or that you own
   it. If it is taken, either claim it or switch to a scoped name
   (e.g. `@domanilabs/syntri`) and update `name` in `typescript/package.json`.

2. **Generate an npm access token.** Account → **Access Tokens** → **Generate
   New Token** → choose **Automation** (bypasses 2FA, meant for CI). Copy it.

3. **Add the token as a GitHub secret.** In the `DomaniLabs/syntri-sdk` repo:
   **Settings → Secrets and variables → Actions → New repository secret**.
   Name it `NPM_TOKEN`, paste the token, save.

## Cutting a release

1. Bump `version` in `typescript/package.json` (e.g. `0.1.0` → `0.1.1`).
2. Commit the bump on `main`.
3. Tag and push, matching the version:

   ```bash
   git tag typescript/v0.1.0
   git push origin --tags
   ```

The `Publish to npm` workflow runs `npm ci`, `npm run build`, then
`npm publish`. Watch it under the repo's **Actions** tab. On success the new
version is live on npm.

## Notes

- The tag version and `package.json` version should match. npm refuses to
  republish a version that already exists.
- CI (`ci.yml`) already runs typecheck, tests, and build on every push and PR,
  so a tag should only be cut from a green `main`.
- To do a dry run locally: `npm run build && npm publish --dry-run`.
