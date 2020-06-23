# Git Mirror

Mirror git repos between services.

## Usage

Configuration is done using a `repos.toml` file:

```toml
[[repo]]
source = "https://$GITHUB_TOKEN@github.com/RealOrangeOne/git-mirror"
destination = "https://$GITHUB_TOKEN@github.com/RealOrangeOne-backup/git-mirror"
```

Environment variables are automatically injected into the `source` and `destination` values.

Now, simply run the script. It will create a `repos` directory, and store the clones in there. For efficiency, these clones are stored so that only changes need to be cloned and pushed in future. `git gc` is automatically run to keep directory sizes down.
