"""Test Phase 3: Bidirectional Sync"""

import sys
sys.path.insert(0, ".")

from core.dsl.document import ScriptDocument
from core.dsl.adapter import ir_to_actions
from core.dsl.adapter import ir_to_actions

# Test code with endif
code = """
flow main {
    if_image("capture_1");
    click(x=1, y=1);
    endif;
}
"""

doc = ScriptDocument()
doc.update_from_code(code)
print("IR valid:", doc.ir.is_valid)
print("Flows:", len(doc.ir.flows))

if doc.ir.flows:
    print("Actions in main:", len(doc.ir.flows[0].actions))
    for a in doc.ir.flows[0].actions:
        print("  -", a.action_type, a.params)
    
    # Test ir_to_actions conversion
    print("\nConverted to Action models:")
    actions = ir_to_actions(doc.ir.flows[0].actions)
    for a in actions:
        print("  -", type(a).__name__)
