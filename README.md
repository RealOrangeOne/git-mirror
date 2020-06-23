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

Now, simply run the script. For efficiency, these clones are stored so that only changes need to be cloned and pushed going forwards. `git gc` is automatically run to keep directory sizes down.

By default, repos are updated every 15 minutes. This can be changed per repo using `interval`.

### Additional settings

`heartbeat`: A HTTP URL to poll to ensure the process is still running. The interval is the smallest interval of all the repos.
`clone_root`: Directory to store clones in. Defaults to `$PWD/repos/`.
