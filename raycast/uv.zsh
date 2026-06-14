#!/bin/zsh

resolve_uv() {
  if [[ -n "${UV_BIN:-}" && -x "${UV_BIN}" ]]; then
    print -r -- "${UV_BIN}"
    return 0
  fi

  local found
  found="$(command -v uv 2>/dev/null || true)"
  if [[ -n "${found}" && -x "${found}" ]]; then
    print -r -- "${found}"
    return 0
  fi

  local extra_path
  extra_path="${HOME}/.local/bin:${HOME}/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
  found="$(PATH="${extra_path}:${PATH}" command -v uv 2>/dev/null || true)"
  if [[ -n "${found}" && -x "${found}" ]]; then
    print -r -- "${found}"
    return 0
  fi

  if [[ -n "${SHELL:-}" && -x "${SHELL}" ]]; then
    found="$("${SHELL}" -lc 'command -v uv' 2>/dev/null | tail -n 1)"
    if [[ -n "${found}" && -x "${found}" ]]; then
      print -r -- "${found}"
      return 0
    fi
  fi

  local candidate
  for candidate in \
    "${HOME}/.local/bin/uv" \
    "${HOME}/.cargo/bin/uv" \
    "/opt/homebrew/bin/uv" \
    "/usr/local/bin/uv" \
    "${HOME}/.asdf/shims/uv" \
    "${HOME}/.local/share/mise/shims/uv" \
    "${HOME}/.nix-profile/bin/uv" \
    "/etc/profiles/per-user/${USER}/bin/uv"
  do
    if [[ -x "${candidate}" ]]; then
      print -r -- "${candidate}"
      return 0
    fi
  done

  return 1
}

SS4D_UV_BIN="$(resolve_uv)" || {
  print -u2 -- "uv not found. Install uv or set UV_BIN=/absolute/path/to/uv."
  return 1
}
