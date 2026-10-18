"""manifest.py -- dataset manifest schema and validation (WEB_INTERFACE_PROTOCOL.md section 3, phase P0).

A manifest describes ANY tabular dataset of curves (a response measured while one variable is swept).
The engine knows only roles; anything domain-specific is supplied by a pack (`derived_by: pack.<name>.<fn>`).

Roles
  group_a, group_b   the two entities whose combination is a "pair" (e.g. material and substance)
  cluster            the independence unit (e.g. paper); drives uncertainty and min_clusters
  series             identifies one curve inside a cluster (optional; part of the curve key)
  sweep_x            the swept variable
  value              a measured value (may be used by response modes)
  covariate          any other numeric or categorical column
  label              descriptive text (shown, not computed on)
Unknown roles are an error. Unit conversions are declared (`units_from` + `convert_to`), never inferred.
"""
import yaml
from jsonschema import Draft202012Validator

ROLES = ["group_a", "group_b", "cluster", "series", "sweep_x", "value", "covariate", "label", "ionic_strength"]

SCHEMA = {
    "type": "object",
    "required": ["schema_version", "dataset", "columns", "response_modes", "curve", "pair_coverage"],
    "additionalProperties": False,
    "properties": {
        "schema_version": {"const": 1},
        "pack": {"type": "string"},
        "dataset": {
            "type": "object", "required": ["id", "title", "source", "status"], "additionalProperties": False,
            "properties": {"id": {"type": "string", "pattern": "^[a-z0-9_]+$"}, "title": {"type": "string"},
                           "source": {"type": "string"}, "status": {"enum": ["exploratory", "confirmed", "demo"]}}},
        "columns": {
            "type": "array", "minItems": 1,
            "items": {
                "type": "object", "required": ["name", "role"], "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"}, "role": {"enum": ROLES}, "units": {"type": "string"},
                    "units_from": {"type": "string"}, "convert_to": {"type": "string"},
                    "derived_by": {"type": "string", "pattern": "^pack\\.[a-z0-9_]+\\.[a-z0-9_]+$"},
                    "range": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
                    "description": {"type": "string"}}}},
        "unit_conversions": {
            "type": "object",
            "additionalProperties": {"type": "object", "additionalProperties": {"type": "number"}}},
        "response_modes": {
            "type": "array", "minItems": 1,
            "items": {
                "type": "object", "required": ["id"], "additionalProperties": False,
                "properties": {"id": {"type": "string"}, "expr": {"type": "string"}, "column": {"type": "string"},
                               "range": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
                               "range_tolerance": {"type": "number"}, "max_out_of_range_frac": {"type": "number"},
                               "description": {"type": "string"}}}},
        "curve": {
            "type": "object", "required": ["key", "x"], "additionalProperties": False,
            "properties": {"key": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                           "x": {"type": "string"}, "x_valid_range": {"type": "array", "items": {"type": "number"}},
                           "min_points": {"type": "integer", "minimum": 1},
                           "min_x_levels": {"type": "integer", "minimum": 1},
                           "x_round": {"type": "integer"}, "min_x_span": {"type": "number"}}},
        "pair_coverage": {
            "type": "object", "required": ["min_points", "min_clusters"], "additionalProperties": False,
            "properties": {"min_points": {"type": "integer"}, "min_clusters": {"type": "integer"},
                           "min_x_span": {"type": "number"}}},
        "validity": {"type": "array", "items": {"type": "object"}},
        "flags": {"type": "array", "items": {"type": "string"}},
    },
}


class ManifestError(ValueError):
    pass


def validate(manifest):
    """Raises ManifestError listing every problem; returns the manifest otherwise."""
    errors = sorted(Draft202012Validator(SCHEMA).iter_errors(manifest), key=lambda e: list(e.path))
    msgs = [f"{'/'.join(map(str, e.path)) or '(top)'}: {e.message}" for e in errors]
    if not msgs:
        names = [c["name"] for c in manifest["columns"]]
        dup = {n for n in names if names.count(n) > 1}
        if dup:
            msgs.append(f"columns: duplicate names {sorted(dup)}")
        roles = [c["role"] for c in manifest["columns"]]
        for needed in ("group_a", "group_b", "cluster", "sweep_x"):
            if roles.count(needed) != 1:
                msgs.append(f"columns: exactly one column with role {needed} is required (found {roles.count(needed)})")
        conv = manifest.get("unit_conversions", {})
        for c in manifest["columns"]:
            if "convert_to" in c and "units_from" not in c:
                msgs.append(f"columns/{c['name']}: convert_to needs units_from (units are declared, never inferred)")
            if "convert_to" in c and c["convert_to"] not in conv:
                msgs.append(f"columns/{c['name']}: no unit_conversions table for target '{c['convert_to']}'")
        for rm in manifest["response_modes"]:
            if ("expr" in rm) == ("column" in rm):
                msgs.append(f"response_modes/{rm['id']}: give exactly one of `column` or `expr`")
            elif "column" in rm and rm["column"] not in names:
                msgs.append(f"response_modes/{rm['id']}: column '{rm['column']}' is not declared")
        for k in manifest["curve"]["key"]:
            if k not in names:
                msgs.append(f"curve/key: '{k}' is not a declared column")
        if manifest["curve"]["x"] not in names:
            msgs.append(f"curve/x: '{manifest['curve']['x']}' is not a declared column")
    if msgs:
        raise ManifestError("invalid manifest:\n  " + "\n  ".join(msgs))
    return manifest


def load(path):
    with open(path, encoding="utf-8") as f:
        return validate(yaml.safe_load(f))


def role_columns(manifest, role):
    return [c["name"] for c in manifest["columns"] if c["role"] == role]


def column(manifest, role):
    cols = role_columns(manifest, role)
    return cols[0] if cols else None
