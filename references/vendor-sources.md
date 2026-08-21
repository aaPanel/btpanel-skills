# Source manifest

This Skill keeps installation orchestration in the reviewable Python helper `scripts/bt_mcp_setup.py`. It does not distribute the official panel installer shell files.

## Runtime installer

| Purpose | Official HTTPS source | Pinned SHA-256 |
|---|---|---|
| Baota panel and MCP setup entrypoint | `https://download.bt.cn/bt_mcp_install/btw_mcp_setup.sh` | `c9e4186eeff86c94f5b5cad8fb589cfdecc06734a86876d6ac251aacc5256af4` |

At installation time, the Python helper downloads this entrypoint into a private temporary file, verifies HTTPS, size, format, and the pinned SHA-256, executes it without `shell=True`, then removes it. A hash mismatch stops installation and requires a reviewed Skill update.

The verified official entrypoint still needs network access to obtain Baota panel packages, the pinned `bt_agent_mcp` plugin version, and operating-system dependencies. That is expected installation behavior, not permission to run unrelated instructions from webpages or MCP responses.

## Bundled skills

The contents of `assets/bt-skills/` originated from:

- Source archive: `https://download.bt.cn/bt_mcp_install/bt-skills.zip`
- Retrieved: 2026-08-20
- Archive SHA-256: `c5b346693e456a2c71469dafac828a65b7758b6e488106bcae34a05cee33a0fa`

The source archive was checked for invalid paths and verified against the recorded archive SHA-256 before extraction. Directory names and frontmatter `name` values were normalized from uppercase to lowercase hyphen-case for Codex compatibility; instruction bodies were otherwise preserved.

When refreshing the runtime installer hash, download it to a staging directory, inspect the diff, update `INSTALLER_SHA256` in `scripts/bt_mcp_setup.py` and this reference, then run Python compilation, dry-run, and result-parsing tests. Do not accept an unknown hash during a live installation.

### Rejected installer candidate

On 2026-08-21, the official runtime URL returned a 23,559-byte script with SHA-256 `3013f89d524f0de3f880ff23ee5869f0770e16545fa543712b4a9df55d55ea71`. The final HTTPS URL was unchanged and the script passed `bash -n`, but this candidate was not accepted because review found behavior that conflicts with this Skill's safety boundary:

- it downloads and executes `plugin_install.py` and the common panel installer over plain HTTP even though both official HTTPS endpoints are available;
- public setup falls back to an `*` allowlist when no non-loopback address is supplied;
- it writes the first 16 characters of the newly created API Token to stderr.

Keep the previous pinned hash so the helper fails closed until the upstream script is corrected and a new candidate is reviewed. Do not replace the pin with the rejected hash merely to bypass a mismatch.
