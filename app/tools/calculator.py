import ast
import operator
from typing import Any

from app.tools.base import BaseTool


class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Evaluate a basic arithmetic expression."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Arithmetic expression, for example: (12 + 8) / 5",
            }
        },
        "required": ["expression"],
        "additionalProperties": False,
    }

    _binary_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    _unary_ops = {
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        expression = arguments.get("expression")
        if not isinstance(expression, str) or not expression.strip():
            return {
                "ok": False,
                "error": "Argument 'expression' must be a non-empty string.",
            }

        tree = ast.parse(expression, mode="eval")
        value = self._eval_node(tree.body)
        return {
            "ok": True,
            "expression": expression,
            "value": value,
        }

    def _eval_node(self, node: ast.AST) -> int | float:
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
            return node.value

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in self._binary_ops:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return self._binary_ops[op_type](left, right)

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in self._unary_ops:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            return self._unary_ops[op_type](self._eval_node(node.operand))

        raise ValueError("Only numeric arithmetic expressions are supported.")
