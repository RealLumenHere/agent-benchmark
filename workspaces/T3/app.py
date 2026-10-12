#!/usr/bin/env python3
"""Simple Flask API with 3 intentional bugs for benchmark testing."""
from flask import Flask, jsonify, request
# BUG 1: Missing import — `json` is used below but not imported
import os

app = Flask(__name__)

# Load config
config_path = os.path.join(os.path.dirname(__file__), "config.json")
with open(config_path) as f:
    config = json.load(f)  # BUG 1 manifests here: NameError: name 'json' is not defined


@app.route("/api/status")
def status():
    return jsonify({"status": "ok", "version": config.get("version", "unknown")})


@app.route("/api/greet")
def greet():
    name = request.args.get("name", "World")
    # BUG 2: Wrong variable name — should be `name` not `user`
    greeting = f"Hello, {user}!"  # noqa: F821
    return jsonify({"greeting": greeting})


@app.route("/api/log")
def write_log():
    message = request.args.get("msg", "no message")
    log_path = os.path.join(os.path.dirname(__file__), "app.log")
    # BUG 3: File opened but never closed (resource leak)
    f = open(log_path, "a")
    f.write(f"{message}\n")
    # Missing: f.close() or use context manager
    return jsonify({"logged": True})


if __name__ == "__main__":
    app.run(debug=True, port=5050)
