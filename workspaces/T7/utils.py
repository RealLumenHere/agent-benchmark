#!/usr/bin/env python3
"""Utility functions."""

def format_name(first, last):
    return f"{first} {last}"

def validate_email(email):
    return "@" in email and "." in email
