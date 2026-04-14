"""
Integration test: verifies that Tenant A cannot retrieve Tenant B's documents.
Requires running Docker Compose services (Qdrant, PostgreSQL, Redis).

Run with: pytest tests/integration/test_tenant_isolation.py -v
"""

import uuid

import pytest

from app.vector_store.embedding import embed_texts, embed_query
from app.vector_store.qdrant_client import (
    collection_name_for_tenant,
    delete_collection,
    ensure_collection,
    search_vectors,
    upsert_chunks,
)


@pytest.fixture
def tenant_a_id():
    return uuid.uuid4()


@pytest.fixture
def tenant_b_id():
    return uuid.uuid4()


@pytest.mark.integration
class TestTenantIsolation:
    def test_cross_tenant_query_returns_zero_results(self, tenant_a_id, tenant_b_id):
        """Tenant A's query should never return Tenant B's documents."""
        # Setup collections
        ensure_collection(tenant_a_id)
        ensure_collection(tenant_b_id)

        try:
            # Insert data for Tenant A
            texts_a = ["Tenant A confidential financial report Q1 2025"]
            embeddings_a = embed_texts(texts_a)
            upsert_chunks(
                tenant_a_id,
                [str(uuid.uuid4())],
                embeddings_a,
                [{"text": texts_a[0], "document_id": str(uuid.uuid4()), "tenant_id": str(tenant_a_id)}],
            )

            # Insert data for Tenant B
            texts_b = ["Tenant B internal engineering roadmap"]
            embeddings_b = embed_texts(texts_b)
            upsert_chunks(
                tenant_b_id,
                [str(uuid.uuid4())],
                embeddings_b,
                [{"text": texts_b[0], "document_id": str(uuid.uuid4()), "tenant_id": str(tenant_b_id)}],
            )

            # Query Tenant A's collection with Tenant B's content
            query_vec = embed_query("Tenant B engineering roadmap")
            results = search_vectors(tenant_a_id, query_vec, top_k=10)

            # Verify no Tenant B content in Tenant A's results
            for result in results:
                payload = result.payload or {}
                assert payload.get("tenant_id") != str(tenant_b_id), (
                    f"Cross-tenant leak detected: Tenant B data found in Tenant A's results"
                )
                assert "Tenant B" not in payload.get("text", ""), (
                    "Cross-tenant leak: Tenant B text in Tenant A results"
                )

            # Query Tenant B's collection with Tenant A's content
            query_vec_2 = embed_query("Tenant A financial report")
            results_2 = search_vectors(tenant_b_id, query_vec_2, top_k=10)

            for result in results_2:
                payload = result.payload or {}
                assert payload.get("tenant_id") != str(tenant_a_id), (
                    "Cross-tenant leak detected: Tenant A data found in Tenant B's results"
                )

        finally:
            # Cleanup
            delete_collection(tenant_a_id)
            delete_collection(tenant_b_id)

    def test_isolation_across_100_queries(self, tenant_a_id, tenant_b_id):
        """Run 100 cross-tenant queries and verify zero leaks."""
        ensure_collection(tenant_a_id)
        ensure_collection(tenant_b_id)

        try:
            # Populate both tenants
            for i in range(10):
                text_a = f"Tenant A document {i}: secret project alpha details"
                text_b = f"Tenant B document {i}: confidential beta initiative"

                emb_a = embed_texts([text_a])
                emb_b = embed_texts([text_b])

                upsert_chunks(
                    tenant_a_id,
                    [str(uuid.uuid4())],
                    emb_a,
                    [{"text": text_a, "document_id": str(uuid.uuid4()), "tenant_id": str(tenant_a_id)}],
                )
                upsert_chunks(
                    tenant_b_id,
                    [str(uuid.uuid4())],
                    emb_b,
                    [{"text": text_b, "document_id": str(uuid.uuid4()), "tenant_id": str(tenant_b_id)}],
                )

            # Run 100 cross-tenant queries
            queries = [f"query about topic {i}" for i in range(100)]
            leaks = 0

            for query in queries:
                q_vec = embed_query(query)

                # Search Tenant A
                results_a = search_vectors(tenant_a_id, q_vec, top_k=5)
                for r in results_a:
                    if (r.payload or {}).get("tenant_id") == str(tenant_b_id):
                        leaks += 1

                # Search Tenant B
                results_b = search_vectors(tenant_b_id, q_vec, top_k=5)
                for r in results_b:
                    if (r.payload or {}).get("tenant_id") == str(tenant_a_id):
                        leaks += 1

            assert leaks == 0, f"Cross-tenant data leaks detected: {leaks}"

        finally:
            delete_collection(tenant_a_id)
            delete_collection(tenant_b_id)
