git config --local user.email "41898282+github-actions[bot]@users.noreply.github.com"
git config --local user.name "github-actions[bot]"

if [[ "$tag_or_release" == "tag" ]]; then
    git checkout ${source_branch}
    git tag -f "${name}" -m "tagged ${source_branch} to ${name} via manual github action"
    # will fail if tag already exists; intentional
    git push origin ${name}

elif [[ "$tag_or_release" == "release" ]]; then
    echo ${token} | gh auth login --with-token
    gh release create ${name} -F changelog.md --target ${source_branch} --title ${name}

else
    echo "bad input"
fi
