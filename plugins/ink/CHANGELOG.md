# Changelog

Tracks the `ink` plugin's `version` in `.claude-plugin/plugin.json`. Bump that field with every change you want installed copies to receive — Claude Code caches plugins by version, so pushing commits alone does not update anyone already on a pinned version. Follow [semver](https://semver.org): MAJOR for breaking changes, MINOR for new features, PATCH for fixes.

## [0.1.0]

Extracted the blog/editorial skills (`post-*`) out of the original single-plugin repo into their own `ink` plugin, sharing the `hexbyte` marketplace with `orc`. No behavioral changes — same skills, same content guide, new home.
