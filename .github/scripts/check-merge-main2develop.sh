git config --local user.email "41898282+github-actions[bot]@users.noreply.github.com"
git config --local user.name "github-actions[bot]"

set -e
git fetch
git checkout develop
git merge origin/main --verbose