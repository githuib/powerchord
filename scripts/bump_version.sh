poetry version "$RELEASE_VERSION"

git config user.name "Github Actions"
git config user.email "github-actions[bot]@users.noreply.github.com"
git add pyproject.toml
git commit -m "Bump version to $RELEASE_VERSION"
# git commit --allow-empty -m "Bump version to $RELEASE_VERSION"
git push
