# syntri-sdk

Official client SDKs for [Syntri](https://github.com/DomaniLabs/Syntri).

| Language | Package | Status |
|---|---|---|
| TypeScript / Node.js | `npm install syntri` | ✅ Available |
| Python | `pip install syntri-sdk` | 🔜 Coming soon |
| Go | `go get github.com/domaniLabs/syntri-sdk/go` | 🔜 Coming soon |

## What is Syntri?

Syntri captures every decision your AI system makes and every outcome
that follows. It identifies which decisions were right, builds training
data from your production traffic automatically, and fine-tunes models
on your data so your AI gets better at your specific use case over time.

Works with any AI system, any domain, any language.

## Quick start

See the README in each language directory:

- [TypeScript / Node.js](./typescript/README.md) — available now
- [Python](./python/README.md) — coming soon
- [Go](./go/README.md) — coming soon

## About these SDKs

Each SDK is a thin client over Syntri's HTTP API (`POST /v1/capture`). It has no
business logic and does not touch your data beyond forwarding it: PII
tokenisation is handled server-side. The SDKs are built for application
developers integrating Syntri into their product.

## Adding a language

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the layout, required methods, test
and CI requirements, and publish-workflow pattern every language SDK follows.
