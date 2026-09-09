"""Local, evidence-first search for long technical PDF documents."""

from .retriever import Retriever, VERSION, build

__all__ = ['Retriever', 'VERSION', 'build']
__version__ = VERSION
