"""Tests for chunker factory and registry."""

import pytest

from app.services.ingestion.chunking import CHUNKER_MAP, get_chunker
from app.services.ingestion.chunking.base import BaseChunker
from app.services.ingestion.chunking.fixed_size import FixedSizeChunker
from app.services.ingestion.chunking.parent_child import ParentChildChunker
from app.services.ingestion.chunking.semantic import SemanticChunker


class TestGetChunker:
    def test_fixed_strategy(self):
        chunker = get_chunker("fixed")
        assert isinstance(chunker, FixedSizeChunker)

    def test_semantic_strategy(self):
        chunker = get_chunker("semantic")
        assert isinstance(chunker, SemanticChunker)

    def test_parent_child_strategy(self):
        chunker = get_chunker("parent_child")
        assert isinstance(chunker, ParentChildChunker)

    def test_unknown_strategy_raises(self):
        with pytest.raises(ValueError, match="Unknown chunking strategy"):
            get_chunker("nonexistent")

    def test_all_registered_chunkers_are_base_subclasses(self):
        for name, cls in CHUNKER_MAP.items():
            assert issubclass(cls, BaseChunker), f"{name} is not a BaseChunker subclass"

    def test_registry_has_three_strategies(self):
        assert set(CHUNKER_MAP.keys()) == {"fixed", "semantic", "parent_child"}
