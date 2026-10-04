#!/bin/sh
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
remote_url=$(git -C "$repo_dir" remote get-url gtk-upstream)

printf '%s\n' "GTK upstream: $remote_url"
git -C "$repo_dir" fetch --quiet gtk-upstream

for branch in main master; do
    if git -C "$repo_dir" show-ref --verify --quiet "refs/remotes/gtk-upstream/$branch"; then
        commit=$(git -C "$repo_dir" rev-parse "gtk-upstream/$branch")
        printf '%s %s\n' "Latest GTK upstream commit:" "$commit"
        printf '%s\n' "Recent upstream changes:"
        git -C "$repo_dir" log --oneline -5 "gtk-upstream/$branch"
        exit 0
    fi
done

printf '%s\n' "Could not determine the upstream default branch." >&2
exit 1
