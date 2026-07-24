import io
from fastapi.testclient import TestClient
from dottednotes.web import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text


def test_index_html_has_measure_numbers_checkbox_and_brl_option():
    # Regression test: the "Include Measure Numbers" checkbox (S11c-3) and
    # the .brl dropdown option (S11c-4) both landed in index.html and were
    # then accidentally reverted by a later commit that touched the same
    # file. The backend keeps working either way, so nothing else in the
    # suite would have caught the UI regression -- this reads the actual
    # served markup instead of just exercising /api/convert.
    response = client.get("/")
    assert response.status_code == 200
    assert 'name="measure_numbers"' in response.text
    assert 'type="checkbox"' in response.text
    assert '<option value="brl">' in response.text

def test_convert_braille_to_lilypond():
    # '⠐⠹' represents C4 in braille music
    file_content = b"\x10\x39" # ASCII braille equivalent of ⠐⠹ if tokenized
    # Or just use raw unicode braille cell text
    file_content = "⠐⠹".encode("utf-8")
    
    file_obj = io.BytesIO(file_content)
    
    response = client.post(
        "/api/convert",
        files={"file": ("test.brf", file_obj, "text/plain")},
        data={
            "target_format": "lilypond",
            "category": "Solo Piano",
            "profile": "standard"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["input_type"] == "braille"
    assert data["target_format"] == "lilypond"
    assert "ly" in data["files"]
    
    # Test downloading the ly file
    job_id = data["job_id"]
    download_response = client.get(f"/api/jobs/{job_id}/ly")
    assert download_response.status_code == 200
    assert "c4" in download_response.text.lower()

def test_convert_braille_to_braille_reformat():
    file_content = "⠐⠹".encode("utf-8")
    file_obj = io.BytesIO(file_content)
    
    response = client.post(
        "/api/convert",
        files={"file": ("test.brf", file_obj, "text/plain")},
        data={
            "target_format": "braille",
            "compression": "minimal",
            "profile": "standard"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["input_type"] == "braille"
    assert data["target_format"] == "braille"
    assert "brf" in data["files"]
    
    # Test downloading the brf file
    job_id = data["job_id"]
    download_response = client.get(f"/api/jobs/{job_id}/brf")
    assert download_response.status_code == 200

def test_convert_invalid_file_limit():
    large_content = b"a" * (10 * 1024 * 1024 + 10) # slightly larger than 10MB
    file_obj = io.BytesIO(large_content)

    response = client.post(
        "/api/convert",
        files={"file": ("test.brf", file_obj, "text/plain")},
        data={"target_format": "lilypond"}
    )

    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"]

def test_convert_rejects_mxl_that_decompresses_past_the_limit():
    # A small compressed upload whose decompressed content would exceed the
    # 10MB cap must be rejected before it ever reaches music21 -- checking
    # only the compressed upload size would miss this (S-ticket: MusicXML
    # upload limit expansion, 2026-07-18).
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("score.xml", b"a" * (11 * 1024 * 1024))
    mxl_bytes = buf.getvalue()
    assert len(mxl_bytes) < 10 * 1024 * 1024  # the upload itself is tiny

    response = client.post(
        "/api/convert",
        files={"file": ("test.mxl", io.BytesIO(mxl_bytes), "application/octet-stream")},
        data={"target_format": "lilypond"}
    )

    assert response.status_code == 400
    assert "decompress" in response.json()["detail"].lower()

def test_convert_invalid_options():
    file_content = "⠐⠹".encode("utf-8")
    
    # Invalid category
    response = client.post(
        "/api/convert",
        files={"file": ("test.brf", io.BytesIO(file_content), "text/plain")},
        data={"target_format": "lilypond", "category": "InvalidCategory"}
    )
    assert response.status_code == 400
    
    # Invalid compression
    response = client.post(
        "/api/convert",
        files={"file": ("test.brf", io.BytesIO(file_content), "text/plain")},
        data={"target_format": "braille", "compression": "invalid_comp"}
    )
    assert response.status_code == 400
    
    # Invalid profile
    response = client.post(
        "/api/convert",
        files={"file": ("test.brf", io.BytesIO(file_content), "text/plain")},
        data={"target_format": "lilypond", "profile": "invalid_profile"}
    )
    assert response.status_code == 400

def test_invalid_job_id():
    response = client.get("/api/jobs/nonexistent-job-id/ly")
    assert response.status_code == 404
    
    response = client.get("/api/jobs/invalid_chars_$_%/ly")
    assert response.status_code == 400


def test_convert_with_measure_numbers_checkbox():
    # '⠐⠹' represents C4 in braille music
    file_content = "⠐⠹".encode("utf-8")
    
    # 1. With measure_numbers=true (in LilyPond)
    response_ly = client.post(
        "/api/convert",
        files={"file": ("test.brf", io.BytesIO(file_content), "text/plain")},
        data={
            "target_format": "lilypond",
            "category": "Solo Piano",
            "profile": "standard",
            "measure_numbers": "true"
        }
    )
    assert response_ly.status_code == 200
    job_id = response_ly.json()["job_id"]
    download_ly = client.get(f"/api/jobs/{job_id}/ly")
    assert "% 1" in download_ly.text  # LilyPond comment for measure 1
    
    # 2. With measure_numbers=true (in Braille - BRL format)
    response_brf = client.post(
        "/api/convert",
        files={"file": ("test.brf", io.BytesIO(file_content), "text/plain")},
        data={
            "target_format": "brl",
            "compression": "none",
            "profile": "standard",
            "measure_numbers": "true"
        }
    )
    assert response_brf.status_code == 200
    job_id = response_brf.json()["job_id"]
    download_brf = client.get(f"/api/jobs/{job_id}/brl")
    assert '⠁⠀' in download_brf.text  # Braille measure number 1 at start of line
    
    # 3. With measure_numbers=false (in Braille - BRL format)
    response_brf_off = client.post(
        "/api/convert",
        files={"file": ("test.brf", io.BytesIO(file_content), "text/plain")},
        data={
            "target_format": "brl",
            "compression": "none",
            "profile": "standard",
            "measure_numbers": "false"
        }
    )
    assert response_brf_off.status_code == 200
    job_id = response_brf_off.json()["job_id"]
    download_brf_off = client.get(f"/api/jobs/{job_id}/brl")
    assert "⠁ " not in download_brf_off.text


def test_convert_brf_and_brl_formats():
    # '⠐⠹' represents C4 in braille music
    file_content = "⠐⠹".encode("utf-8")
    
    # 1. Convert to target_format="brf" (ASCII braille)
    response_brf = client.post(
        "/api/convert",
        files={"file": ("test.brf", io.BytesIO(file_content), "text/plain")},
        data={
            "target_format": "brf",
            "compression": "none",
            "profile": "standard",
            "measure_numbers": "true"
        }
    )
    assert response_brf.status_code == 200
    job_id = response_brf.json()["job_id"]
    download_brf = client.get(f"/api/jobs/{job_id}/brf")
    assert download_brf.status_code == 200
    text_brf = download_brf.text
    # Content must contain only ASCII braille chars
    assert all(ord(c) < 128 or c in ('\n', '\r', '\f', '\t') for c in text_brf)
    
    # 2. Convert to target_format="brl" (Unicode braille)
    response_brl = client.post(
        "/api/convert",
        files={"file": ("test.brf", io.BytesIO(file_content), "text/plain")},
        data={
            "target_format": "brl",
            "compression": "none",
            "profile": "standard",
            "measure_numbers": "true"
        }
    )
    assert response_brl.status_code == 200
    job_id = response_brl.json()["job_id"]
    download_brl = client.get(f"/api/jobs/{job_id}/brl")
    assert download_brl.status_code == 200
    text_brl = download_brl.text
    # Content should contain Unicode braille cells (e.g. U+2800 range)
    assert any(0x2800 <= ord(c) <= 0x28FF for c in text_brl)
