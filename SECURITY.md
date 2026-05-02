# Security Policy

## Supported Scope

This project supports security reports for vulnerabilities in the repository's
code, configuration, API behavior, frontend behavior, notebook execution, and
documentation that could expose secrets, corrupt artifacts, bypass safety
guardrails, or enable unsafe operational use.

Raw third-party datasets are not redistributed in this repository. Report data
licensing or privacy concerns when project code or documentation could cause
improper handling of those sources.

## Reporting a Vulnerability

If the issue is not sensitive, open a GitHub issue with clear reproduction
steps. If disclosure would create risk, contact the repository owner privately
through GitHub and avoid posting exploit details publicly.

Helpful reports include:

- Affected file, endpoint, notebook, or workflow.
- Steps to reproduce the issue.
- Expected and actual behavior.
- Impact assessment.
- Suggested fix, if known.

## Safety Boundary

Do not submit reports or examples that include tactical targeting, weapon
construction, evasion methods, or operational attack guidance. Keep examples
minimal, synthetic, and aggregate whenever possible.

## Response Expectations

Maintainers will triage reports by severity and safety impact. High-risk
issues that affect secrets, data handling, or safety guardrails should be
prioritized before feature work.
