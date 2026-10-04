# Contribution and update policy

The `main` branch is protected by review. Upstream changes from the GTK
repository and KDE/Aurorae improvements must not be applied directly.

For every proposed update:

1. Fetch the relevant upstream without modifying `main`.
2. Create a dedicated branch for that update.
3. Review the complete diff, including license and attribution changes.
4. Test both the GTK and KDE/Aurorae installations as applicable.
5. Open one Pull Request/Merge Request for that branch.
6. Merge only after personal approval.

The update checker is intentionally read-only with respect to tracked theme
files. It reports upstream commits but does not merge, copy, or overwrite
local changes.
