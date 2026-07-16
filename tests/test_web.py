import io
from fastapi.testclient import TestClient
from dottednotes.web import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text

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
    large_content = b"a" * (1024 * 1024 + 10) # slightly larger than 1MB
    file_obj = io.BytesIO(large_content)
    
    response = client.post(
        "/api/convert",
        files={"file": ("test.brf", file_obj, "text/plain")},
        data={"target_format": "lilypond"}
    )
    
    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"]

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
