"""Build metadata for the desktop app. Overwritten by the GitHub Actions
workflow at build time. In the cloud/dev environment these defaults are used."""

VERSION = "dev"       # human-readable version / release tag
BUILD_TIME = ""       # ISO-8601 UTC timestamp of the CI build (empty in dev)
GIT_SHA = "dev"       # short commit SHA the build was made from
REPO = ""             # "owner/repo" — used to query GitHub Releases for updates
