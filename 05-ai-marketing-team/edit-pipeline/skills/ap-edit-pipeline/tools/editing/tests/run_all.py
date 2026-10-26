#!/usr/bin/env python3
"""Run every test in this folder and print one honest verdict.

Order matters: the two that need nothing installed run first, so a machine with
no engine still gets a real answer about whether the logic is sound.

  test_cutcut.py         the cut logic. Must pass. No tools needed.
  test_props_builder.py  the overlay props contract. Must pass. No tools needed.
  test_chain.py          media rules, silence maths, render and export planning,
                         transcript normalising. Parts skip without ffmpeg.
  test_e2e_synthetic.py  the real chain on media it makes itself. Skips cleanly
                         when the machine has no voice generator or no engine.

Run:  python3 tests/run_all.py
Exit 0 means every test that could run, passed.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ORDER = [
    "test_cutcut.py",
    "test_props_builder.py",
    "test_chain.py",
    "test_e2e_synthetic.py",
]


def main():
    results = []
    for name in ORDER:
        path = os.path.join(HERE, name)
        print(f"\n===== {name} =====", flush=True)
        code = subprocess.run([sys.executable, path]).returncode
        results.append((name, code))

    print("\n===== verdict =====")
    failed = [name for name, code in results if code != 0]
    for name, code in results:
        print(f"{'pass' if code == 0 else 'FAIL'}  {name}")
    if failed:
        print(f"\n{len(failed)} test file(s) failed. Do not edit anything until this is green.")
        return 1
    print("\nAll green. Skipped tests are honest skips, not passes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
