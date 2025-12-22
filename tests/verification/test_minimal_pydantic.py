"""
Minimal test to isolate Pydantic validation issue.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

print("Step 1: Import models...")
from core.models import ClickImage, GraphNode, Action

print("Step 2: Create ClickImage directly...")
click = ClickImage(asset_id="test_button")
print(f"  Created: {click}")
print(f"  Action field value: {click.action}")
print(f"  Type: {type(click)}")

print("\nStep 3: Verify ClickImage is an Action...")
# Can't use isinstance with Union types
print(f"  Skipping isinstance check (Union types don't support it)")

print("\nStep 4: Create GraphNode with ClickImage...")
try:
    node = GraphNode(
        id="test-123",
        action=click,
        x=0,
        y=0
    )
    print(f"  ✓ SUCCESS: {node}")
except Exception as e:
    print(f"  ✗ FAILED: {type(e).__name__}")
    print(f"  Error: {e}")
    
print("\nStep 5: Try with model_dump/model_validate...")
try:
    click_dict = click.model_dump()
    print(f"  Dumped to dict: {click_dict}")
    
    node = GraphNode(
        id="test-123",
        action=click_dict,  # Pass as dict
        x=0,
        y=0
    )
    print(f"  ✓ SUCCESS with dict: {node}")
except Exception as e:
    print(f"  ✗ FAILED: {type(e).__name__}")
    print(f"  Error: {e}")

print("\nStep 6: Check Action union...")
from typing import get_args
action_types = get_args(Action)
print(f"  Action union has {len(action_types)} types")
print(f"  ClickImage in union? {ClickImage in action_types}")
