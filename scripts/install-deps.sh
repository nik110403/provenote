#!/usr/bin/env bash
# install-deps.sh - install the external tools the provenote helpers need.
# Usage: install-deps.sh [--workflow pdf|build|all] [--typst] [--dry-run] [--yes]
# macOS: brew. Debian/Ubuntu: apt-get. Fedora: dnf. Others: manual hints, exit 3.
# Exit: doctor's code at the end; 2 bad usage; 3 unsupported OS; 4 Homebrew missing;
# 1 declined/failed install. Package names mirror plugins/provenote/bin/doctor.
# Note: older apt releases may ship pandoc < 2.11; doctor reports that after install.
# --typst installs via brew only; on apt/dnf a manual hint is printed instead.
set -u

workflow=all
typst=0
dry=0
yes=0
while [ $# -gt 0 ]; do
	case "$1" in
	--workflow)
		[ $# -ge 2 ] || { echo "install-deps: --workflow needs a value" >&2; exit 2; }
		workflow=$2
		shift
		;;
	--typst) typst=1 ;;
	--dry-run) dry=1 ;;
	--yes | -y) yes=1 ;;
	-h | --help)
		sed -n '2,8p' "$0"
		exit 0
		;;
	*)
		echo "install-deps: unknown option: $1" >&2
		exit 2
		;;
	esac
	shift
done
case "$workflow" in
pdf | build | all) ;;
*)
	echo "install-deps: --workflow must be pdf, build or all" >&2
	exit 2
	;;
esac

# No dirname: PATH may be minimal. A bare name (bash install-deps.sh) has no slash.
src=${BASH_SOURCE[0]}
case "$src" in */*) src_dir=${src%/*} ;; *) src_dir=. ;; esac
script_dir=$(CDPATH='' cd -- "$src_dir" && pwd) || exit 1
doctor="$script_dir/../plugins/provenote/bin/doctor"
if [ ! -f "$doctor" ]; then
	echo "install-deps: doctor not found at $doctor (run from a full provenote checkout)" >&2
	exit 1
fi

# What is wanted: "tool:package-key" pairs; skip tools already on PATH.
want=()
{ [ "$workflow" = pdf ] || [ "$workflow" = all ]; } && want+=(pdftotext)
{ [ "$workflow" = build ] || [ "$workflow" = all ]; } && want+=(pandoc)
[ "$typst" = 1 ] && want+=(typst)
missing=()
for tool in ${want[@]+"${want[@]}"}; do
	if type -P "$tool" >/dev/null 2>&1; then
		echo "skip: $tool already installed"
	else
		missing+=("$tool")
	fi
done

# OS detection: uname, then os-release (RK_OS_RELEASE overrides the path for tests).
os_release=${RK_OS_RELEASE:-/etc/os-release}
kernel=$(uname -s 2>/dev/null)
manager=""
case "$kernel" in
Darwin) manager=brew ;;
Linux)
	id="" id_like=""
	if [ -r "$os_release" ]; then
		while IFS='=' read -r key value; do
			value=${value#\"}
			value=${value%\"}
			case "$key" in
			ID) id=$value ;;
			ID_LIKE) id_like=$value ;;
			esac
		done <"$os_release"
	fi
	case " $id $id_like " in
	*" debian "* | *" ubuntu "*) manager=apt ;;
	*" fedora "* | *" rhel "*) manager=dnf ;;
	esac
	;;
esac
if [ -z "$manager" ]; then
	{
		echo "install-deps: unsupported system (${kernel:-unknown}). Install manually:"
		echo "  poppler (provides pdftotext), pandoc >= 2.11, optionally Typst >= 3.1"
		echo "Then check with: python3 plugins/provenote/bin/doctor --workflow $workflow"
	} >&2
	exit 3
fi

sudo_cmd=""
if [ "$manager" != brew ] && [ "${EUID:-1}" -ne 0 ]; then sudo_cmd="sudo "; fi
pkgs=()
typst_hint=0
# ${arr[@]+...}: bash 3.2 + set -u errors on a bare empty-array expansion
for tool in ${missing[@]+"${missing[@]}"}; do
	case "$manager:$tool" in
	apt:pdftotext | dnf:pdftotext) pkgs+=(poppler-utils) ;;
	brew:pdftotext) pkgs+=(poppler) ;;
	apt:typst | dnf:typst) typst_hint=1 ;;  # not in common apt/dnf repos
	*) pkgs+=("$tool") ;;
	esac
done

cmds=()
if [ ${#pkgs[@]} -gt 0 ]; then
	case "$manager" in
	brew) cmds+=("brew install ${pkgs[*]}") ;;
	apt)
		cmds+=("${sudo_cmd}apt-get update")
		cmds+=("${sudo_cmd}apt-get install -y ${pkgs[*]}")
		;;
	dnf) cmds+=("${sudo_cmd}dnf install -y ${pkgs[*]}") ;;
	esac
fi

if [ "$manager" = brew ] && [ ${#cmds[@]} -gt 0 ] && ! command -v brew >/dev/null 2>&1; then
	echo "install-deps: Homebrew is not installed. Install it from https://brew.sh, then rerun this script." >&2
	exit 4
fi

if [ "$typst_hint" = 1 ]; then
	echo "note: typst is not in common apt/dnf repos; install it manually: https://github.com/typst/typst#installation"
fi
if [ ${#cmds[@]} -eq 0 ]; then
	echo "Nothing to install."
else
	echo "Commands to run:"
	for c in "${cmds[@]}"; do echo "  $c"; done
fi
if [ "$dry" = 1 ]; then exit 0; fi

if [ ${#cmds[@]} -gt 0 ]; then
	if [ "$yes" != 1 ]; then
		printf 'Run these commands? [y/N] '
		read -r answer || answer=""
		case "$answer" in
		y | Y | yes | YES) ;;
		*) echo "Aborted."; exit 1 ;;
		esac
	fi
	for c in "${cmds[@]}"; do
		# shellcheck disable=SC2086 # commands are built from fixed words
		$c || { echo "install-deps: failed: $c" >&2; exit 1; }
	done
fi

python3 "$doctor" --workflow "$workflow"
