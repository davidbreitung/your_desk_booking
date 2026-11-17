# Home Assistant Custom Integration Template

Reusable starter for Home Assistant custom integrations, including agent instructions, requirements, status tracking and CI checks.

## Start a new project
1. On GitHub, enable **Settings > General > Template repository** for this repository.
2. Select **Use this template > Create a new repository**.
3. Replace the example domain `example_integration` and metadata in `custom_components/example_integration/manifest.json`.
4. Complete `REQUIREMENTS.md` before implementation.
5. Follow `AGENTS.md` and update `STATUS.md` with every relevant development task.

## Local installation
Copy `custom_components/<domain>` to Home Assistant's `/config/custom_components/<domain>`, restart Home Assistant and add the integration via Settings > Devices & services if applicable.

This starter is a scaffold, not a finished integration. Do not deploy it unchanged.
