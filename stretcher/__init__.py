"""Analysis pipeline for the pneumatic cell-stretcher device paper.

Replaces the divergent notebook copies (Static/Cyclic trackpy notebooks,
synchronization*.ipynb, plot_*_images.ipynb). Single source of truth for
per-run parameters: experiments.yaml at the repo root.
"""

from stretcher.registry import load_registry

__all__ = ["load_registry"]
