# Private AI 🕵️ - Project Tasks

This document outlines the tasks required to make the Private AI proxy fully usable, reliable, and ready for further development.

## Phase 1: Stabilize Core Functionality & UI (High Priority)

### UI Integration & Backend Connection
- **Proxy Controls:**
  - [ ] Connect `Start Proxy` button to `/start_proxy` endpoint.
  - [ ] Connect `Stop Proxy` button to `/stop_proxy` endpoint.
  - [ ] Ensure `Proxy Status` dynamically reflects actual state via `/api/stats` or `is_proxy_running()`.
  - [ ] Connect `Test Connection` button fully (already partially implemented).
  - [x] Implement Certificate Download & Manual Install Modal (`/download_cert`, UI modal, removed script logic). Task: Verify modal instructions are accurate for all listed OS/browsers.
  - [ ] Connect `Install Certificate` button fully (already partially implemented).
- **Protection Summary:**
  - [ ] Replace static values with dynamic data fetched from `/api/stats` or database.
- **Privacy Controls:**
  - [ ] Load initial state of toggles from `.env` or configuration.
  - [ ] Connect `Save Settings` button to backend logic to update `.env` or configuration.
  - [ ] Ensure toggle changes affect proxy behavior in real-time or upon restart.
- **Test Your Text Area:**
  - [ ] Replace simple JS regex with an API call to `/api/process-text`.
  - [ ] Ensure `/api/process-text` uses the actual `pii_transform.py` logic, not just basic regex.
  - [ ] Display actual entities found count.
- **Domain Management:**
  - [ ] Load domains dynamically based on selected category.
  - [ ] Connect `Add Domain` button to `/add_domain` endpoint.
  - [ ] Connect `Remove` buttons to `/remove_domain/<domain>` endpoint.
  - [ ] Connect `Save Domains` button to persist changes (potentially via `save_domain_blocklist` or similar).
  - [ ] Implement filtering/display logic based on the `Provider Category` dropdown.
- **AI Server Management (if separate pages exist):**
  - [ ] Verify full CRUD functionality for AI servers via the UI (`/ai_servers/*` routes).

### Proxy Core Integration & Reliability
- [ ] Verify `pii_transform.py` logic is correctly invoked within `proxy_intercept.py` for requests/responses.
- [ ] Test handling of different content types (JSON, form data, plain text) in the proxy.
- [ ] Ensure robust handling of various AI API formats (OpenAI, Anthropic, Google - as shown in UI tabs). Test request transformation and response restoration.
- [ ] Verify `custom_patterns.json` patterns are loaded and applied correctly by the proxy.
- [ ] Verify `ai_domains.json` (or `domain_blocklist.txt`) is used correctly for domain blocking/allowing.
- [ ] Verify `ai_servers.json` configuration is used for routing or potential future features.

### Configuration Management
- [ ] Test loading and saving of `custom_patterns.json`.
- [ ] Test loading and saving of `domain_blocklist.txt` / `ai_domains.json`.
- [ ] Test loading and saving of `ai_servers.json`.
- [ ] Test reading and updating of `.env` settings via `update_env_setting`.
- [ ] Ensure configuration changes are reflected in the proxy's behavior (may require proxy restart logic).

### Error Handling & Logging
- [ ] Review and enhance logging across `app.py`, `ai_proxy.py`, `proxy_intercept.py`, `pii_transform.py`, `utils.py`.
- [ ] Implement more specific error handling and user feedback in the UI for failed operations (proxy start/stop, saving settings, etc.).
- [ ] Ensure consistency in logging formats.

## Phase 2: Testing & Quality Assurance (Medium Priority)

- [ ] Develop Unit Test Suite for core modules (`pii_transform.py`, `utils.py`, `codename_generator.py`).
- [ ] Develop Integration Test Suite for:
  - Proxy request/response lifecycle with PII transformation.
  - API endpoint functionality in `app.py`.
  - Configuration loading and saving.
- [ ] Setup CI/CD using GitHub Actions to run tests automatically.
- [ ] Add code coverage reporting (e.g., `coverage.py`).

## Phase 3: Documentation & Polish (Medium Priority)

- [ ] Review and update all documentation in `/docs` for accuracy after refactoring and stabilization.
- [ ] Ensure detective theme 🕵️ is consistently applied where appropriate.
- [ ] Enhance `/docs/quickstart.md` with more detailed examples.
- [ ] Add architecture diagrams to `/docs` (if `images/architecture-overview.png` is outdated or missing).
- [ ] Complete `/docs/ide-ai-integration.md` with concrete examples.
- [ ] Populate `/docs/troubleshooting.md` with common issues and solutions (e.g., certificate errors, connection problems).
- [ ] Refine UI/UX in `one_page.html` for clarity and ease of use.

## Phase 4: Security Hardening (Medium Priority)

- [ ] Conduct security review of `app.py`