from __future__ import annotations

from typing import Any

from flask import jsonify


def ok(data: Any, status_code: int = 200):
    return jsonify({"success": True, "data": data, "error": None}), status_code


def err(message: str, code: str = "ERROR", status_code: int = 400):
    return (
        jsonify({"success": False, "data": None, "error": {"message": message, "code": code}}),
        status_code,
    )

