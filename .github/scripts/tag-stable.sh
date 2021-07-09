git config --local user.email "41898282+github-actions[bot]@users.noreply.github.com"
git config --local user.name "github-actions[bot]"

set -e
git checkout main
rev=`git rev-parse --short main`
git tag -f "stable" -m "stable tag updated to rev ${rev} on main"
git push origin :stable
git push origin stable