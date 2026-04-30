#!/bin/sh
set -eu

base_dir="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
entrypoint_file="$base_dir/entrypoint.sh"
http_template="$base_dir/nginx.conf.http.template"
https_template="$base_dir/nginx.conf.https.template"

for file in "$entrypoint_file" "$http_template" "$https_template"; do
  if [ ! -f "$file" ]; then
    echo "Missing required nginx file: $file"
    exit 1
  fi
done

grep -q 'envsubst' "$entrypoint_file"
grep -q 'proxy_pass http://frontend:3000;' "$http_template"
grep -q 'proxy_pass http://backend:8000;' "$http_template"
grep -q 'proxy_pass http://frontend:3000;' "$https_template"
grep -q 'proxy_pass http://backend:8000;' "$https_template"

echo "Nginx smoke checks passed."
