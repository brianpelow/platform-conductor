# platform-conductor

> Meta-orchestrator for the brianpelow platform — coordinates 15 agents, detects failures, and publishes weekly health summaries.

![CI](https://github.com/brianpelow/platform-conductor/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-green.svg)

## Overview

`platform-conductor` sits above all 15 portfolio repos and orchestrates them
as a coherent platform. It runs nightly to verify every agent workflow
succeeded, opens GitHub issues automatically when failures are detected, and
publishes a weekly state-of-the-platform summary to GitHub Discussions every
Monday morning.

## What it does

**Nightly (03:00 UTC)**
- Polls GitHub Actions API for last 24h workflow runs across all 15 repos
- Classifies each run as success, failure, or skipped
- Opens a GitHub issue on any repo where the nightly agent failed
- Updates platform health scores in docs/

**Weekly (Monday 08:00 UTC)**
- Aggregates nightly health data from the past 7 days
- Computes platform-wide reliability score
- Generates AI-powered weekly summary
- Posts to GitHub Discussions as a pinned weekly thread

## Commands

```bash
conductor status           # Show current health of all 15 repos
conductor report           # Generate weekly platform report
conductor discuss --post   # Post weekly summary to Discussions
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache 2.0