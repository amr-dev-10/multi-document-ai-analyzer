from backend.embeddings.local import cosine, embed_text
from backend.rag.chunker import chunk_pages


def test_embedding_similarity_prefers_related_text():
    query = embed_text("payment terms invoice")
    related = embed_text("invoice payment shall be completed in 45 days")
    unrelated = embed_text("the office has a blue chair")
    assert cosine(query, related) > cosine(query, unrelated)


def test_chunk_pages_keeps_page_metadata():
    chunks = chunk_pages([{"page": 4, "text": "word " * 260}], chunk_words=100, overlap_words=10)
    assert len(chunks) == 3
    assert chunks[0].page == 4
    assert chunks[1].index == 1

