from math import ceil


LINES_PER_PAGE = 42


def escape_pdf_text(value):
    text = str(value or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return text.encode("latin-1", "replace").decode("latin-1")


def build_simple_text_pdf(title, lines):
    title_line = escape_pdf_text(title)
    safe_lines = [escape_pdf_text(line) for line in lines]
    page_count = max(1, ceil(max(len(safe_lines), 1) / LINES_PER_PAGE))
    grouped_lines = []
    for index in range(page_count):
        start = index * LINES_PER_PAGE
        end = start + LINES_PER_PAGE
        page_lines = safe_lines[start:end] or [""]
        grouped_lines.append(page_lines)

    objects = []
    page_ids = []
    font_object_id = 3
    next_object_id = 4

    for page_number, page_lines in enumerate(grouped_lines, start=1):
        content_lines = [
            "BT",
            "/F1 10 Tf",
            "50 800 Td",
            f"({title_line}) Tj",
            "0 -18 Td",
            f"(Page {page_number} of {page_count}) Tj",
            "0 -22 Td",
        ]
        for line in page_lines:
            content_lines.append(f"({line}) Tj")
            content_lines.append("0 -14 Td")
        content_lines.append("ET")

        stream = "\n".join(content_lines).encode("latin-1", "replace")
        page_object_id = next_object_id
        content_object_id = next_object_id + 1
        page_ids.append(page_object_id)
        next_object_id += 2

        objects.append(
            (
                content_object_id,
                b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream),
            )
        )
        objects.append(
            (
                page_object_id,
                (
                    f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                    f"/Resources << /Font << /F1 {font_object_id} 0 R >> >> "
                    f"/Contents {content_object_id} 0 R >>"
                ).encode("latin-1"),
            )
        )

    page_refs = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    base_objects = [
        (1, b"<< /Type /Catalog /Pages 2 0 R >>"),
        (2, f"<< /Type /Pages /Count {len(page_ids)} /Kids [{page_refs}] >>".encode("latin-1")),
        (3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"),
    ]
    ordered_objects = sorted(base_objects + objects, key=lambda item: item[0])

    pdf_chunks = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    for object_id, content in ordered_objects:
        offsets.append(sum(len(chunk) for chunk in pdf_chunks))
        pdf_chunks.append(f"{object_id} 0 obj\n".encode("latin-1"))
        pdf_chunks.append(content)
        pdf_chunks.append(b"\nendobj\n")

    xref_position = sum(len(chunk) for chunk in pdf_chunks)
    object_count = len(ordered_objects) + 1
    pdf_chunks.append(f"xref\n0 {object_count}\n".encode("latin-1"))
    pdf_chunks.append(b"0000000000 65535 f \n")
    for object_id in range(1, object_count):
        pdf_chunks.append(f"{offsets[object_id]:010d} 00000 n \n".encode("latin-1"))
    pdf_chunks.append(
        (
            "trailer\n"
            f"<< /Size {object_count} /Root 1 0 R >>\n"
            f"startxref\n{xref_position}\n%%EOF"
        ).encode("latin-1")
    )
    return b"".join(pdf_chunks)
