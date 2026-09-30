# Findings

- Bootstrap: the origin is configured as git@github.com:saitakarcesme/PocketLore.git on main. No physical Android device is provided.
- Two RTX 3090 GPUs report 24 GB each. One local GPU job at a time is the initial policy. Model-list availability alone is not generation evidence.
- Installed Codex CLI is 0.158.0; explicit exec/resume help has been inspected. Existing authentication and default model are retained.
- Prior atlas notes show successful Android plumbing can coexist with unusable answers. Useful grounded output needs its own evidence.
- User linger is enabled. The shell lacks user bus environment variables; the service installer must provide the existing /run/user UID bus path.
