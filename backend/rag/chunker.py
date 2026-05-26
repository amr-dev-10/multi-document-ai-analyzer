from dataclasses import dataclass


@dataclass
class ChunkItem:
    index: int
    page: int | None
    text: str


def chunk_pages(pages: list[dict], chunk_words: int = 180, overlap_words: int = 35) -> list[ChunkItem]:
    chunks: list[ChunkItem] = []
    index = 0
    step = max(1, chunk_words - overlap_words)
    for page in pages:
        words = (page.get("text") or "").split()
        if not words:
            continue
        for start in range(0, len(words), step):
            text = " ".join(words[start : start + chunk_words]).strip()
            if text:
                chunks.append(ChunkItem(index=index, page=page.get("page"), text=text))
                index += 1
            if start + chunk_words >= len(words):
                break
    return chunks

