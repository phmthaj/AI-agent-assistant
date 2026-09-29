from typing import Any

from app.tools.base import BaseTool


class UnitConverterTool(BaseTool):
    name = "unit_converter"
    description = "Convert values between common length, mass, and temperature units."
    parameters = {
        "type": "object",
        "properties": {
            "value": {
                "type": "number",
                "description": "Numeric value to convert.",
            },
            "from_unit": {
                "type": "string",
                "description": "Source unit, for example km, m, cm, mile, kg, g, lb, c, f, k.",
            },
            "to_unit": {
                "type": "string",
                "description": "Target unit, for example km, m, cm, mile, kg, g, lb, c, f, k.",
            },
        },
        "required": ["value", "from_unit", "to_unit"],
        "additionalProperties": False,
    }

    _length_to_meter = {
        "mm": 0.001,
        "cm": 0.01,
        "m": 1.0,
        "km": 1000.0,
        "in": 0.0254,
        "ft": 0.3048,
        "yd": 0.9144,
        "mile": 1609.344,
    }
    _mass_to_kg = {
        "mg": 0.000001,
        "g": 0.001,
        "kg": 1.0,
        "ton": 1000.0,
        "oz": 0.028349523125,
        "lb": 0.45359237,
    }
    _temperature_units = {"c", "f", "k"}

    async def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        value = arguments.get("value")
        from_unit = self._normalize_unit(arguments.get("from_unit"))
        to_unit = self._normalize_unit(arguments.get("to_unit"))

        if not isinstance(value, int | float):
            return {"ok": False, "error": "Argument 'value' must be numeric."}

        if from_unit in self._length_to_meter and to_unit in self._length_to_meter:
            meters = float(value) * self._length_to_meter[from_unit]
            converted = meters / self._length_to_meter[to_unit]
            category = "length"
        elif from_unit in self._mass_to_kg and to_unit in self._mass_to_kg:
            kilograms = float(value) * self._mass_to_kg[from_unit]
            converted = kilograms / self._mass_to_kg[to_unit]
            category = "mass"
        elif from_unit in self._temperature_units and to_unit in self._temperature_units:
            converted = self._convert_temperature(float(value), from_unit, to_unit)
            category = "temperature"
        else:
            return {
                "ok": False,
                "error": f"Unsupported conversion: {from_unit} to {to_unit}",
            }

        return {
            "ok": True,
            "category": category,
            "value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "converted": converted,
        }

    def _normalize_unit(self, unit: Any) -> str:
        if not isinstance(unit, str):
            return ""
        aliases = {
            "meter": "m",
            "meters": "m",
            "kilometer": "km",
            "kilometers": "km",
            "gram": "g",
            "grams": "g",
            "kilogram": "kg",
            "kilograms": "kg",
            "pound": "lb",
            "pounds": "lb",
            "celsius": "c",
            "fahrenheit": "f",
            "kelvin": "k",
        }
        normalized = unit.strip().lower()
        return aliases.get(normalized, normalized)

    def _convert_temperature(
        self,
        value: float,
        from_unit: str,
        to_unit: str,
    ) -> float:
        if from_unit == "c":
            celsius = value
        elif from_unit == "f":
            celsius = (value - 32) * 5 / 9
        else:
            celsius = value - 273.15

        if to_unit == "c":
            return celsius
        if to_unit == "f":
            return celsius * 9 / 5 + 32
        return celsius + 273.15
