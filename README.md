# Git Mirror

Mirror git repositories between services.

## Usage

Configuration is done using a `repositories.toml` file:

```toml
[[repository]]
source = "https://$GITHUB_TOKEN@github.com/RealOrangeOne/git-mirror"
destination = "https://$GITHUB_TOKEN@github.com/RealOrangeOne-backup/git-mirror"
```

Environment variables are automatically injected into the `source` and `destination` values.

Now, simply run the script. For efficiency, these clones are stored so that only changes need to be cloned and pushed going forwards. `git gc` is automatically run to keep directory sizes down.

To just run the mirror once, run using `--once`.

### Additional settings

`heartbeat`: A HTTP URL to poll to ensure the process is still running. The interval is the smallest interval of all the repositories. Works nicely with [healthchecks.io](https://healthchecks.io/).

`clone_root`: Directory to store repositories in. Defaults to `$PWD/repositories/`.

`interval`: How often repositories are checked (in seconds). Defaults to 15 minutes.
