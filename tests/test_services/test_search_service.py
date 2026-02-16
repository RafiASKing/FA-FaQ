from app.ports.vector_store_port import VectorDocument, VectorSearchResult
from app.services.search_service import SearchResult, SearchService


class _FakeVectorStore:
    def __init__(self, query_results=None, all_docs=None):
        self.query_results = query_results or []
        self.all_docs = all_docs or []
        self.last_where = None
        self.was_queried = False

    def query(self, query_embedding, n_results=50, where=None):
        self.was_queried = True
        self.last_where = where
        return self.query_results

    def get_all(self, include_documents=False):
        return self.all_docs


def test_search_filters_by_relevance_and_sorts(monkeypatch):
    fake_store = _FakeVectorStore(query_results=[
        VectorSearchResult(id="a", metadata={"tag": "ED", "judul": "A"}, distance=0.30),  # 70
        VectorSearchResult(id="b", metadata={"tag": "OPD", "judul": "B"}, distance=0.05),  # 95
        VectorSearchResult(id="c", metadata={"tag": "IPD", "judul": "C"}, distance=0.50),  # 50
    ])

    monkeypatch.setattr("app.services.search_service.container.get_vector_store", lambda: fake_store)
    monkeypatch.setattr("app.services.search_service.EmbeddingService.generate_query_embedding", lambda _: [0.1, 0.2])
    monkeypatch.setattr("app.services.search_service.TagManager.get_tag_color", lambda _: "#123456")

    results = SearchService.search("cara login")

    assert [r.id for r in results] == ["b"]
    assert results[0].score == 95.0


def test_search_applies_tag_prefilter(monkeypatch):
    fake_store = _FakeVectorStore(query_results=[])

    monkeypatch.setattr("app.services.search_service.container.get_vector_store", lambda: fake_store)
    monkeypatch.setattr("app.services.search_service.EmbeddingService.generate_query_embedding", lambda _: [0.1])

    SearchService.search("query", filter_tag="ED", min_score=0)

    assert fake_store.last_where == {"tag": "ED"}


def test_search_returns_empty_when_embedding_unavailable(monkeypatch):
    fake_store = _FakeVectorStore(query_results=[
        VectorSearchResult(id="x", metadata={}, distance=0.1)
    ])

    monkeypatch.setattr("app.services.search_service.container.get_vector_store", lambda: fake_store)
    monkeypatch.setattr("app.services.search_service.EmbeddingService.generate_query_embedding", lambda _: None)

    results = SearchService.search("query")

    assert results == []
    assert fake_store.was_queried is False


def test_search_for_bot_respects_allowed_modules(monkeypatch):
    seeded = [
        SearchResult("1", "ED", "a", "", "", "none", "", 90.0, "score-high", "#f00"),
        SearchResult("2", "OPD", "b", "", "", "none", "", 85.0, "score-high", "#0f0"),
    ]
    monkeypatch.setattr(SearchService, "search", classmethod(lambda cls, query, filter_tag=None: seeded))

    results = SearchService.search_for_bot("query", allowed_modules=["OPD"])

    assert len(results) == 1
    assert results[0].id == "2"


def test_get_unique_tags_returns_sorted_unique(monkeypatch):
    fake_store = _FakeVectorStore(all_docs=[
        VectorDocument(id="1", metadata={"tag": "OPD"}),
        VectorDocument(id="2", metadata={"tag": "ED"}),
        VectorDocument(id="3", metadata={"tag": "OPD"}),
    ])

    monkeypatch.setattr("app.services.search_service.container.get_vector_store", lambda: fake_store)

    tags = SearchService.get_unique_tags()

    assert tags == ["ED", "OPD"]
