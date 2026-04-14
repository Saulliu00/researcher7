#!/usr/bin/env python3
"""
End-to-end pipeline test with a fake LLM.
Runs the real pipeline (data fetch, correlation, paper search, script gen, save, CSV log)
but uses a FakeLLM so no real LLM is needed.

Usage:  python tests/run_e2e.py
"""
import csv
import json
import os
import shutil
import sys
import tempfile

# Setup paths
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from llm_providers.base import LLMProvider


class FakeLLM(LLMProvider):
    """Fake LLM that returns realistic placeholder podcast text."""
    _call_count = 0

    @property
    def name(self):
        return "FakeLLM"

    @property
    def model(self):
        return "fake-test-1.0"

    @property
    def supports_long_context(self):
        return False

    def generate(self, prompt):
        self._call_count += 1
        section = (
            "Hey, this is Saul, and welcome back to another episode. "
            "Today we are diving into some fascinating trends that caught my eye. "
            "Artificial intelligence continues to dominate the conversation, and for good reason. "
            "The technology is advancing at a pace that few of us could have predicted even a decade ago. "
            "From healthcare to entertainment, AI is reshaping the way we live and work. "
            "But it is not just about the technology itself. It is about what it means for all of us. "
            "Climate change remains one of the most pressing issues of our time. "
            "People are searching for solutions, and the scientific community is responding. "
            "Renewable energy sources are becoming more efficient and more affordable. "
            "Quantum computing promises to unlock computational power we can barely imagine. "
            "These trends are not isolated. They are deeply interconnected in ways that reveal "
            "something profound about where our society is heading. "
            "The research paper we are looking at today sheds light on exactly these connections. "
            "It shows how advances in one field can cascade into breakthroughs in another. "
            "What I find most exciting is the real-world applications that are already emerging. "
            "Think about smart grids powered by AI that optimize renewable energy distribution. "
            "Or quantum algorithms that could accelerate drug discovery. The future is not as far "
            "away as we think. Let me walk you through some of the key findings. "
        )
        # Double it to produce ~360 words per section
        return (section + section)[:2200]


def main():
    # Use a temp output dir so we don't pollute real outputs
    tmp_dir = os.path.join(tempfile.gettempdir(), "researcher7_e2e_test")
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir, exist_ok=True)

    print("=" * 60)
    print("RESEARCHER7 END-TO-END TEST (FakeLLM)")
    print("=" * 60)
    print(f"Output dir: {tmp_dir}\n")

    # Import the real pipeline
    from main import Researcher7

    fake_llm = FakeLLM()
    researcher = Researcher7(llm_provider=fake_llm)

    # Run the full pipeline
    output_path = researcher.run(
        num_trends=15,
        country="united_states",
        output_dir=tmp_dir,
    )

    # ================================================================
    # VALIDATION
    # ================================================================
    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)

    passed = 0
    failed = 0

    def check(condition, label):
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label}")

    # 1. Script file
    check(os.path.exists(output_path), f"Script file exists")
    with open(output_path, "r", encoding="utf-8") as f:
        script = f.read()
    wc = len(script.split())
    check(wc > 500, f"Script has {wc:,} words (>500)")
    check("Researcher7 Voice Script" in script, "Script header present")
    check("FakeLLM" in script, "FakeLLM in header metadata")
    check("fake-test-1.0" in script, "Model name in header")

    # 2. CSV run log
    csv_path = os.path.join(tmp_dir, "run_log.csv")
    check(os.path.exists(csv_path), "CSV log exists")
    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    check(len(rows) == 1, f"CSV has 1 row (got {len(rows)})")
    if rows:
        row = rows[0]
        check(row["step1_country"] == "united_states", f"CSV step1_country = {row['step1_country']}")
        check(row["step2_topic"] != "", f"CSV step2_topic = {row['step2_topic']}")
        check(row["step3_paper_title"] != "", f"CSV step3_paper = {row['step3_paper_title'][:50]}")
        check(int(row["step4_word_count"]) > 0, f"CSV step4_word_count = {row['step4_word_count']}")
        check(row["step1_provider"] != "", f"CSV step1_provider = {row['step1_provider']}")
        check(row["step4_provider"] != "", f"CSV step4_provider = {row['step4_provider']}")
        check(row["output_script_path"] != "", f"CSV output_script_path present")

    # 3. Autosave
    autosave_dir = os.path.join("outputs", "autosave")
    section_files = sorted(
        f for f in os.listdir(autosave_dir) if f.startswith("section_")
    )
    check(len(section_files) == 10, f"Autosave has {len(section_files)} section files")

    progress_path = os.path.join(autosave_dir, "progress.json")
    check(os.path.exists(progress_path), "progress.json exists")
    with open(progress_path, "r") as f:
        progress = json.load(f)
    check(
        progress["completed_sections"] == 10,
        f"Progress: {progress['completed_sections']}/10 sections",
    )

    # 4. LLM call count
    check(fake_llm._call_count == 10, f"LLM called {fake_llm._call_count}x (expected 10)")

    # Summary
    total = passed + failed
    print(f"\n{'=' * 60}")
    if failed == 0:
        print(f"ALL {total} CHECKS PASSED - Pipeline works end-to-end!")
    else:
        print(f"{passed}/{total} passed, {failed} FAILED")
    print("=" * 60)

    # Cleanup
    shutil.rmtree(tmp_dir)
    print(f"Temp dir cleaned up.")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
