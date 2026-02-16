import pandas as pd

from app.ports.vector_store_port import VectorDocument
from app.services.faq_service import FaqService


class _FakeVectorStore:
    def __init__(self):
        self.ids = []
        self.docs = {}
        self.upsert_calls = []
        self.deleted_id = None

    def get_all_ids(self):
        return self.ids

    def upsert(self, doc_id, embedding, document, metadata):
        self.upsert_calls.append({
            "doc_id": doc_id,
            "embedding": embedding,
            "document": document,
            "metadata": metadata,
        })
        self.docs[str(doc_id)] = VectorDocument(id=str(doc_id), metadata=metadata, document=document)

    def get_by_id(self, doc_id, include_documents=True):
        return self.docs.get(str(doc_id))

    def delete(self, doc_id):
        self.deleted_id = str(doc_id)
        return True

    def get_all(self, include_documents=True):
        return list(self.docs.values())


def test_get_next_id_uses_highest_numeric(monkeypatch):
    store = _FakeVectorStore()
    store.ids = ["1", "abc", "10", "5"]
    monkeypatch.setattr("app.services.faq_service.container.get_vector_store", lambda: store)

    assert FaqService._get_next_id() == "11"


def test_upsert_create_generates_id_and_persists_metadata(monkeypatch):
    store = _FakeVectorStore()
    store.ids = ["2"]

    monkeypatch.setattr("app.services.faq_service.container.get_vector_store", lambda: store)
    monkeypatch.setattr(
        "app.services.faq_service.EmbeddingService.build_faq_document",
        lambda **kwargs: ([0.1, 0.2], "embedded-doc"),
    )

    new_id = FaqService.upsert(
        tag="ED",
        judul="Cara login",
        jawaban="Langkah login",
        keywords="login emr",
        source_url="https://example.com",
    )

    assert new_id == "3"
    assert store.upsert_calls[0]["doc_id"] == "3"
    assert store.upsert_calls[0]["metadata"]["tag"] == "ED"
    assert store.upsert_calls[0]["metadata"]["judul"] == "Cara login"


def test_get_by_id_returns_enriched_payload(monkeypatch):
    store = _FakeVectorStore()
    store.docs["9"] = VectorDocument(
        id="9",
        metadata={"tag": "OPD", "judul": "Tes"},
        document="doc-body",
    )
    monkeypatch.setattr("app.services.faq_service.container.get_vector_store", lambda: store)

    result = FaqService.get_by_id("9")

    assert result is not None
    assert result["id"] == "9"
    assert result["document"] == "doc-body"
    assert result["tag"] == "OPD"


def test_delete_cascades_image_cleanup(monkeypatch):
    store = _FakeVectorStore()
    store.docs["4"] = VectorDocument(
        id="4",
        metadata={"path_gambar": "images/a.jpg;images/b.jpg"},
    )
    called = {"paths": None}

    monkeypatch.setattr("app.services.faq_service.container.get_vector_store", lambda: store)
    monkeypatch.setattr("app.services.faq_service.ImageHandler.delete_images", lambda p: called.update({"paths": p}))

    ok = FaqService.delete("4")

    assert ok is True
    assert called["paths"] == "images/a.jpg;images/b.jpg"
    assert store.deleted_id == "4"


def test_count_by_tag_filters_dataframe(monkeypatch):
    df = pd.DataFrame([
        {"Tag": "ED", "Judul": "A"},
        {"Tag": "ED", "Judul": "B"},
        {"Tag": "OPD", "Judul": "C"},
    ])
    monkeypatch.setattr(FaqService, "get_all_as_dataframe", classmethod(lambda cls: df))

    assert FaqService.count_by_tag("ED") == 2
    assert FaqService.count_by_tag("LAB") == 0
