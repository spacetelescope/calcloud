git config --local user.email "41898282+github-actions[bot]@users.noreply.github.com"
git config --local user.name "github-actions[bot]"

set -e
git checkout develop
rev=`git rev-parse --short develop`
git tag -f "latest" -m "latest tag updated to rev ${rev} on develop"
git push origin :latest
git push origin latest