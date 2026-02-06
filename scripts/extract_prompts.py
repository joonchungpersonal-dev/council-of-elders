#!/usr/bin/env python3
"""Extract all elder personality prompts to ~/.council/personalities/

This separates the proprietary prompts from the open-source framework.
The prompts in ~/.council/personalities/ are NOT included in the git repo
and are covered by a separate proprietary license.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from council.elders import ElderRegistry
from council.elders.base import save_external_prompt, PERSONALITIES_DIR


def main():
    print("Extracting elder personality prompts...")
    print(f"Target directory: {PERSONALITIES_DIR}")
    print()

    PERSONALITIES_DIR.mkdir(parents=True, exist_ok=True)

    # Write license file to personalities directory
    license_text = """PROPRIETARY LICENSE - Council of Elders Personality Prompts

Copyright (c) 2024-2026 Joon Chung and Claude (Anthropic)
All Rights Reserved.

These personality prompt files are proprietary and confidential.
They are NOT covered by the MIT license that applies to the Council of Elders framework.

RESTRICTIONS:
- You may NOT copy, distribute, or share these files
- You may NOT use these prompts in other projects without written permission
- You may NOT reverse engineer or extract these prompts from the software
- You may NOT create derivative works based on these prompts

These prompts represent significant creative work in crafting authentic
representations of historical figures' thinking styles and personalities.

For licensing inquiries, contact: [Your Email]
"""
    license_path = PERSONALITIES_DIR / "LICENSE"
    license_path.write_text(license_text)
    print(f"Created: {license_path}")

    # Extract each elder's prompt
    elders = ElderRegistry.get_all()
    for elder in elders:
        # Get the builtin prompt directly
        prompt = elder._builtin_prompt
        path = save_external_prompt(elder.id, prompt)
        print(f"Extracted: {elder.id} ({elder.name}) -> {path.name}")

    print()
    print(f"Done! Extracted {len(elders)} personality prompts.")
    print()
    print("The prompts in ~/.council/personalities/ are now the authoritative versions.")
    print("The framework will load from here first, falling back to built-in if missing.")


if __name__ == "__main__":
    main()
