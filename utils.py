def chunk_text_by_size(text, max_chars=1500, overlap=200):
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) + 2 <= max_chars:
            current_chunk += para + "\n\n"
        else:
            chunks.append(current_chunk.strip())
            if overlap:
                overlap_text = current_chunk[-overlap:]
                current_chunk = overlap_text + para + "\n\n"
            else:
                current_chunk = para + "\n\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
