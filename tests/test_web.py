import io
from pathlib import Path

from fastapi.testclient import TestClient
from dottednotes.web import app

client = TestClient(app)
FIXTURES = Path(__file__).parent / "fixtures"

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


def test_index_html_links_to_readme_documentation():
    # The header, footer, and post-translation instrument dialog should
    # each link out to the README's own documentation rather than leaving
    # users to guess what an option (or the instrument popup) does.
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    readme_usage_url = "https://github.com/judithhinlung/DottedNotes/blob/main/README.md#usage"
    readme_options_url = "https://github.com/judithhinlung/DottedNotes/blob/main/README.md#customization-options"
    assert html.count(readme_options_url) == 2  # header + instrument dialog
    assert readme_usage_url in html

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


# --- S12-3: BANA Sec. 24 single-line format -- post-translation instrument
# selection, with a title-based default inferred automatically ---

# Time sig 4/4, one margin-numbered segment (measure 1): BANA 24.1.1's
# number-sign-prefixed margin number followed by a single space then music.
_SINGLE_LINE_BRF = "⠀⠀⠼⠙⠲\n⠼⠁⠀⠐⠹\n".encode("utf-8")

# Same, but with a title mentioning an instrument the parser can infer from.
_SINGLE_LINE_BRF_WITH_TITLE = (
    "⠀⠀⠠⠍⠑⠇⠕⠙⠽⠀⠋⠕⠗⠀⠧⠊⠕⠇⠊⠝\n⠀⠀⠼⠙⠲\n⠼⠁⠀⠐⠹\n"
).encode("utf-8")


def test_list_instruments_endpoint_returns_full_general_midi_list():
    response = client.get("/api/instruments")
    assert response.status_code == 200
    instruments = response.json()["instruments"]
    assert len(instruments) == 128
    assert "violin" in instruments
    assert "french horn" in instruments


def test_convert_single_staff_solo_brf_needs_instrument_selection_and_infers_piano():
    # No title to infer from -> falls back to piano, but the frontend is
    # still told a confirm/override popup is worth showing.
    response = client.post(
        "/api/convert",
        files={"file": ("solo.brf", io.BytesIO(_SINGLE_LINE_BRF), "text/plain")},
        data={"target_format": "lilypond"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["needs_instrument_selection"] is True
    assert data["inferred_instrument"] == "acoustic grand"
    assert data["parts"] == [{"name": "Acoustic Grand", "needs_instrument": False}]

    job_id = data["job_id"]
    ly = client.get(f"/api/jobs/{job_id}/ly").text
    assert '\\set Staff.instrumentName = "Acoustic Grand"' in ly
    assert '\\set Staff.midiInstrument = "acoustic grand"' in ly


def test_convert_single_staff_solo_brf_infers_instrument_from_title():
    response = client.post(
        "/api/convert",
        files={"file": ("solo.brf", io.BytesIO(_SINGLE_LINE_BRF_WITH_TITLE), "text/plain")},
        data={"target_format": "lilypond"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["needs_instrument_selection"] is True
    assert data["inferred_instrument"] == "violin"

    job_id = data["job_id"]
    ly = client.get(f"/api/jobs/{job_id}/ly").text
    assert '\\set Staff.instrumentName = "Violin"' in ly
    assert '\\set Staff.midiInstrument = "violin"' in ly


def test_convert_multi_staff_score_does_not_need_instrument_selection():
    response = client.post(
        "/api/convert",
        files={"file": ("fengyang_flower_drum.brf", open(FIXTURES / "fengyang_flower_drum.brf", "rb"))},
        data={"target_format": "lilypond"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["needs_instrument_selection"] is False
    assert data["inferred_instrument"] is None


def test_set_instrument_overrides_inferred_default():
    response = client.post(
        "/api/convert",
        files={"file": ("solo.brf", io.BytesIO(_SINGLE_LINE_BRF_WITH_TITLE), "text/plain")},
        data={"target_format": "lilypond"},
    )
    job_id = response.json()["job_id"]

    override = client.post(f"/api/jobs/{job_id}/instrument", data={"instrument": "flute"})
    assert override.status_code == 200
    assert override.json()["parts"] == [{"name": "Flute", "needs_instrument": False}]

    ly = client.get(f"/api/jobs/{job_id}/ly").text
    assert '\\set Staff.instrumentName = "Flute"' in ly
    assert '\\set Staff.midiInstrument = "flute"' in ly


def test_set_instrument_with_unknown_name_returns_400():
    response = client.post(
        "/api/convert",
        files={"file": ("solo.brf", io.BytesIO(_SINGLE_LINE_BRF), "text/plain")},
        data={"target_format": "lilypond"},
    )
    job_id = response.json()["job_id"]

    override = client.post(f"/api/jobs/{job_id}/instrument", data={"instrument": "kazoo"})
    assert override.status_code == 400
    assert "Unknown instrument" in override.json()["detail"]


def test_set_instrument_rejects_job_with_no_selection_pending():
    # A multi-staff score never sets needs_instrument_selection, so the
    # override endpoint has nothing to apply it to.
    response = client.post(
        "/api/convert",
        files={"file": ("fengyang_flower_drum.brf", open(FIXTURES / "fengyang_flower_drum.brf", "rb"))},
        data={"target_format": "lilypond"},
    )
    job_id = response.json()["job_id"]

    override = client.post(f"/api/jobs/{job_id}/instrument", data={"instrument": "violin"})
    assert override.status_code == 400
    assert "instrument selection pending" in override.json()["detail"]


def test_set_part_instrument_for_extracted_piano_hand():
    with open(FIXTURES / "fingering_melody.brf", "rb") as f:
        response = client.post(
            "/api/convert",
            files={"file": ("fingering_melody.brf", f)},
            data={"target_format": "lilypond"},
        )
    data = response.json()
    assert data["parts"][0] == {"name": "right hand", "needs_instrument": True}
    job_id = data["job_id"]

    override = client.post(f"/api/jobs/{job_id}/parts/0/instrument", data={"instrument": "acoustic grand"})
    assert override.status_code == 200
    assert override.json()["name"] == "Acoustic Grand"

    ly = client.get(f"/api/jobs/{job_id}/parts/0/ly").text
    assert '\\set Staff.instrumentName = "Acoustic Grand"' in ly
    assert '\\set Staff.midiInstrument = "acoustic grand"' in ly
