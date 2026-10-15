#!/usr/bin/env python3
"""Run existing checks in disposable copies, leaving archived evidence untouched."""
import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGNS = {
    "original": "iac2027-vector-compression-kit",
    "reassessment": "ccsds123-independent-reassessment",
    "revision": "ccsds123-revision",
}


def prepare(label):
    runs = ROOT / "runs"
    runs.mkdir(exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix=label + "-", dir=runs))
    shutil.copytree(ROOT / "research", run / "research")
    print("Prepared run:", run, flush=True)
    return run


def invoke(work, script, *arguments):
    env = dict(os.environ)
    env.setdefault("LANDSAT_DATA_DIR", str(ROOT / "data/landsat"))
    env.setdefault("CCSDS_DATA_DIR", str(ROOT / "data/hypso"))
    env.setdefault("CCSDS_NTNU_DIR", str(ROOT / "external/ccsds123_issue_2_verification_model"))
    subprocess.run([sys.executable, script, *arguments], cwd=work, env=env, check=True)


def require_x86_avx2():
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "AMD64"):
        raise SystemExit("This host check requires Linux/x86-64 with AVX2.")
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.exists() or "avx2" not in cpuinfo.read_text().lower().split():
        raise SystemExit("AVX2 was not detected. Do not run the native host kernels here.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "host-smoke", "sanitizer-check", "rvv-build", "renode-check"))
    parser.add_argument("campaign", nargs="?", choices=CAMPAIGNS)
    args = parser.parse_args()
    if args.action == "prepare":
        if args.campaign is None:
            parser.error("prepare requires original, reassessment or revision")
    elif args.campaign is not None:
        parser.error("campaign applies only to prepare")
    if args.action in ("host-smoke", "sanitizer-check"):
        require_x86_avx2()
    if args.action == "host-smoke" and not shutil.which(os.environ.get("CC", "gcc")):
        raise SystemExit("Install GCC or set CC to a compatible compiler.")
    if args.action in ("sanitizer-check", "rvv-build", "renode-check") and not shutil.which("clang-18"):
        raise SystemExit("This preserved driver requires clang-18 on PATH.")
    if args.action in ("rvv-build", "renode-check"):
        if not (os.environ.get("LLD") or shutil.which("ld.lld")):
            raise SystemExit("Set LLD to a RISC-V-capable LLVM linker or install ld.lld on PATH.")
    if args.action == "renode-check" and not (os.environ.get("RENODE") or shutil.which("renode")):
        raise SystemExit("Set RENODE to Renode1.17 with RVV support or install it on PATH.")

    run = prepare(args.action if args.action != "prepare" else args.campaign)
    if args.action == "prepare":
        print("Campaign directory:", run / "research" / CAMPAIGNS[args.campaign])
        print("Set data/reference/CPU environment variables before launching the campaign drivers.")
        return
    if args.action == "host-smoke":
        work = run / "research" / CAMPAIGNS["original"]
        invoke(work, "src/build.py", "host")
        invoke(work, "src/run_suite.py", "--repeats", "0", "--out", str(run / "smoke-results"))
    elif args.action == "sanitizer-check":
        invoke(run / "research" / CAMPAIGNS["reassessment"], "check_new_baselines.py")
    else:
        work = run / "research" / CAMPAIGNS["revision"]
        invoke(work, "build_revision.py")
        if args.action == "renode-check":
            invoke(work, "run_renode.py")
    print("Check completed. Fresh outputs are in", run, flush=True)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from error
