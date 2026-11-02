# SPDX-License-Identifier: AGPL-3.0-only
"""Read-only engineering views; no statistical or proof claims are inferred."""
from .render import render_search, render_timeline

__all__ = ["render_search", "render_timeline"]
__version__ = "0.0.1"
