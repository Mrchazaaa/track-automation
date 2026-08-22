#!/usr/bin/env python3
"""Backward-compatible launcher; use ``python -m track_automation.cli`` instead."""

from track_automation.cli import main
from track_automation.lalal_client import LalalAI
from track_automation.workflow import split_instr

__all__ = ["LalalAI", "main", "split_instr"]


if __name__ == "__main__":
    main()
