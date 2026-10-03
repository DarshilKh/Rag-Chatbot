"""Tests for document upload, listing, renaming, and deletion."""
from tests.conftest import upload_file


def test_upload_markdown_document(client, sample_md_path):
    response = upload_file(client, sample_md_path, "handbook.md")

    assert response.status_code == 201
    body = response.json()["document"]
    assert body["filename"] == "handbook.md"
    assert body["status"] == "ready"
    assert body["chunk_count"] > 0
    assert body["size_bytes"] > 0


def test_upload_docx_document(client, sample_docx_path):
    response = upload_file(
        client,
        sample_docx_path,
        "phoenix.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    assert response.status_code == 201
    assert response.json()["document"]["status"] == "ready"


def test_upload_rejects_unsupported_extension(client, tmp_path):
    bad_file = tmp_path / "malware.exe"
    bad_file.write_bytes(b"not a real document")

    response = upload_file(client, bad_file, content_type="application/octet-stream")

    assert response.status_code == 415
    assert response.json()["error_code"] == "unsupported_file_type"


def test_upload_rejects_empty_file(client, tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b"")

    response = upload_file(client, empty_file, content_type="text/plain")

    assert response.status_code == 415


def test_upload_rejects_oversized_file(client, tmp_path, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)
    big_file = tmp_path / "big.txt"
    big_file.write_bytes(b"x" * (2 * 1024 * 1024))

    response = upload_file(client, big_file, content_type="text/plain")

    assert response.status_code == 413
    assert response.json()["error_code"] == "file_too_large"


def test_list_documents_empty_by_default(client):
    response = client.get("/documents")

    assert response.status_code == 200
    assert response.json() == {"documents": [], "total": 0}


def test_list_documents_after_upload(client, sample_md_path):
    upload_file(client, sample_md_path)

    response = client.get("/documents")

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_get_single_document(client, sample_md_path):
    doc_id = upload_file(client, sample_md_path).json()["document"]["id"]

    response = client.get(f"/documents/{doc_id}")

    assert response.status_code == 200
    assert response.json()["id"] == doc_id


def test_get_document_not_found(client):
    response = client.get("/documents/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error_code"] == "document_not_found"


def test_rename_document(client, sample_md_path):
    doc_id = upload_file(client, sample_md_path).json()["document"]["id"]

    response = client.patch(f"/documents/{doc_id}", json={"new_filename": "renamed.md"})

    assert response.status_code == 200
    assert response.json()["filename"] == "renamed.md"


def test_rename_rejects_forbidden_characters(client, sample_md_path):
    doc_id = upload_file(client, sample_md_path).json()["document"]["id"]

    response = client.patch(f"/documents/{doc_id}", json={"new_filename": "bad/name.md"})

    assert response.status_code == 422  # Pydantic validation error


def test_rename_rejects_empty_name(client, sample_md_path):
    doc_id = upload_file(client, sample_md_path).json()["document"]["id"]

    response = client.patch(f"/documents/{doc_id}", json={"new_filename": "   "})

    assert response.status_code == 422


def test_delete_document(client, sample_md_path):
    doc_id = upload_file(client, sample_md_path).json()["document"]["id"]

    response = client.delete(f"/documents/{doc_id}")
    assert response.status_code == 200

    follow_up = client.get(f"/documents/{doc_id}")
    assert follow_up.status_code == 404


def test_delete_document_removes_it_from_the_list(client, sample_md_path):
    doc_id = upload_file(client, sample_md_path).json()["document"]["id"]

    client.delete(f"/documents/{doc_id}")

    assert client.get("/documents").json()["total"] == 0
