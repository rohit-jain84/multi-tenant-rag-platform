"""
Load test: 100 concurrent users submitting queries.

Usage:
  locust -f tests/load/locustfile.py --host http://localhost:8000

Then open http://localhost:8089 to configure and run the test.
Set Users=100, Spawn Rate=10.
"""

import json
import os

from locust import HttpUser, between, task


class QueryUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self):
        # Use environment variable or default test API key
        self.api_key = os.environ.get("TEST_API_KEY", "rag_test_key")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @task(3)
    def query_hybrid(self):
        self.client.post(
            "/api/v1/query",
            headers=self.headers,
            json={
                "question": "What are the main findings in the report?",
                "search_type": "hybrid",
            },
        )

    @task(2)
    def query_dense_only(self):
        self.client.post(
            "/api/v1/query",
            headers=self.headers,
            json={
                "question": "Summarize the key points of the document.",
                "search_type": "dense_only",
            },
        )

    @task(1)
    def query_with_filters(self):
        self.client.post(
            "/api/v1/query",
            headers=self.headers,
            json={
                "question": "What does the report say about performance?",
                "search_type": "hybrid",
                "filters": {"categories": ["reports"]},
            },
        )

    @task(1)
    def list_documents(self):
        self.client.get(
            "/api/v1/documents",
            headers=self.headers,
        )

    @task(1)
    def health_check(self):
        self.client.get("/health")
