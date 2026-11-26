#!/bin/bash
# Publish a prebuilt Vue release or switch back to an existing release.
set -euo pipefail

web_root=${GOODS_MDM_WEB_ROOT:-/var/www/goods-mdm}
releases="$web_root/releases"
current="$web_root/current"

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 publish BUILD_DIR | rollback RELEASE_ID" >&2
  exit 2
fi

umask 022
mkdir -p -- "$releases"
exec 9>"$releases/.lock"
flock 9

case "$1" in
  publish)
    input=$(realpath -e -- "$2")
    test -f "$input/index.html"
    test -d "$input/assets"
    if find "$input" -mindepth 1 ! -type f ! -type d -print -quit | read -r unexpected; then
      echo "Build contains a non-regular file: $unexpected" >&2
      exit 1
    fi
    release=$(mktemp -d "$releases/$(date -u +%Y%m%dT%H%M%SZ).XXXXXXXX")
    cp -R -- "$input/index.html" "$input/assets" "$release/"
    chmod -R a+rX "$release"
    ;;
  rollback)
    [[ "$2" =~ ^[0-9]{8}T[0-9]{6}Z\.[[:alnum:]]{8}$ ]]
    release="$releases/$2"
    test -d "$release" && test ! -L "$release"
    test -f "$release/index.html"
    ;;
  *)
    echo "Unknown command: $1" >&2
    exit 2
    ;;
esac

switch=$(mktemp -d "$web_root/.switch.XXXXXXXX")
trap 'unlink "$switch/current" 2>/dev/null || true; rmdir "$switch"' EXIT
ln -s "releases/$(basename "$release")" "$switch/current"
mv -Tf -- "$switch/current" "$current"
printf '%s\n' "$(basename "$release")"
