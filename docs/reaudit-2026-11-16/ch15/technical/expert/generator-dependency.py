"""Isolate the original weekly intensity expression and fix all inputs except final health."""
import ast
import hashlib
import math
from pathlib import Path

root=Path(__file__).resolve().parents[5]
source=(root/'tools/gen_final2.py').read_text()
module=ast.parse(source)
node=next(n.value for n in ast.walk(module) if isinstance(n,ast.Assign)
          and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='factor'
          and ast.unparse(n.value)=='np.exp(0.4 * health)')
expr=compile(ast.Expression(node),'generator.weekly_factor','eval')
print('source hash',hashlib.sha256(source.encode()).hexdigest(), 'line',node.lineno,'source',ast.unparse(node))
for final in [-.5,.5]:
    early_health=0.0
    factor=eval(expr,{'np':math,'health':final})
    correct_for_early_week=eval(expr,{'np':math,'health':early_health})
    print('same early health',early_health,'final health',final,'historical factor',factor,'as-of-early-week factor',correct_for_early_week)
