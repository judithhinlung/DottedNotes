document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('convert-form');
    const fileInput = document.getElementById('music-file');
    const uploadZone = document.getElementById('upload-zone');
    const fileNameDisplay = document.getElementById('file-name-display');
    const targetFormatSelect = document.getElementById('target_format');
    const submitBtn = document.getElementById('submit-btn');
    const submitBtnLabel = document.getElementById('submit-btn-label');
    const statusAnnouncer = document.getElementById('status-announcement');

    // Progress bar
    const progressContainer = document.getElementById('progress-container');
    const progressTrack = document.getElementById('progress-track');
    const progressFill = document.getElementById('progress-fill');
    const progressLabel = document.getElementById('progress-label');

    // UI Option Groups
    const groupCategory = document.getElementById('group-category');
    const groupCompression = document.getElementById('group-compression');
    const groupPageNumbers = document.getElementById('group-page-numbers');
    const groupMeasureNumbering = document.getElementById('group-measure-numbering');
    const groupOctaveEveryMeasure = document.getElementById('group-octave-every-measure');
    const groupIncludeClefSign = document.getElementById('group-include-clef-sign');
    const groupFullMeasureRepeat = document.getElementById('group-full-measure-repeat');
    const groupMinRepeatedMeasures = document.getElementById('group-min-repeated-measures');
    const pageNumbersCheckbox = document.getElementById('page_numbers');

    // Results Section
    const resultSection = document.getElementById('result-section');
    const statusBadge = document.getElementById('status-badge');
    const downloadLinks = document.getElementById('download-links');
    const compileLogContainer = document.getElementById('compile-log-container');
    const compileLog = document.getElementById('compile-log');

    // Validation Section
    const validationSection = document.getElementById('validation-section');
    const validationSummary = document.getElementById('validation-summary');
    const validationTbody = document.getElementById('validation-tbody');

    // UI Status regions and wrappers
    const downloadStatusRegion = document.getElementById('download-status-region');
    const compileStatusRegion = document.getElementById('compile-status-region');
    const validationStatusRegion = document.getElementById('validation-status-region');
    const validationTableWrapper = document.getElementById('validation-table-wrapper');

    function updateSectionState(section, state, details = {}) {
        if (section === 'validation') {
            if (state === 'no_file') {
                validationStatusRegion.textContent = 'No file uploaded.';
                validationStatusRegion.classList.remove('hidden');
                validationSummary.classList.add('hidden');
                validationTableWrapper.classList.add('hidden');
            } else if (state === 'awaiting') {
                validationStatusRegion.textContent = 'Awaiting translation.';
                validationStatusRegion.classList.remove('hidden');
                validationSummary.classList.add('hidden');
                validationTableWrapper.classList.add('hidden');
            } else if (state === 'in_progress') {
                validationStatusRegion.textContent = 'Translation in progress...';
                validationStatusRegion.classList.remove('hidden');
                validationSummary.classList.add('hidden');
                validationTableWrapper.classList.add('hidden');
            } else if (state === 'empty') {
                validationStatusRegion.textContent = '';
                validationStatusRegion.classList.add('hidden');
                validationSummary.textContent = 'No warnings or errors flagged.';
                validationSummary.classList.remove('hidden');
                validationTableWrapper.classList.add('hidden');
            } else if (state === 'present') {
                validationStatusRegion.textContent = '';
                validationStatusRegion.classList.add('hidden');
                validationSummary.textContent = `Found ${details.count} BANA formatting rule violation(s). Review recommendations below.`;
                validationSummary.classList.remove('hidden');
                validationTableWrapper.classList.remove('hidden');
            }
        } else if (section === 'downloads') {
            if (state === 'no_file') {
                statusBadge.textContent = 'No File';
                statusBadge.className = 'badge neutral';
                downloadStatusRegion.textContent = 'No file uploaded.';
                downloadStatusRegion.classList.remove('hidden');
                downloadLinks.classList.add('hidden');
            } else if (state === 'awaiting') {
                statusBadge.textContent = 'Awaiting Translation';
                statusBadge.className = 'badge neutral';
                downloadStatusRegion.textContent = 'Awaiting translation.';
                downloadStatusRegion.classList.remove('hidden');
                downloadLinks.classList.add('hidden');
            } else if (state === 'in_progress') {
                statusBadge.textContent = 'Translating';
                statusBadge.className = 'badge neutral';
                downloadStatusRegion.textContent = 'Translation in progress...';
                downloadStatusRegion.classList.remove('hidden');
                downloadLinks.classList.add('hidden');
            } else if (state === 'empty') {
                statusBadge.textContent = 'Success';
                statusBadge.className = 'badge success';
                downloadStatusRegion.textContent = 'No output files generated.';
                downloadStatusRegion.classList.remove('hidden');
                downloadLinks.classList.add('hidden');
            } else if (state === 'present') {
                const badgeText = details.badgeText || 'Success';
                const badgeClass = details.badgeClass || 'success';
                statusBadge.textContent = badgeText;
                statusBadge.className = `badge ${badgeClass}`;
                downloadStatusRegion.textContent = '';
                downloadStatusRegion.classList.add('hidden');
                downloadLinks.classList.remove('hidden');
            } else if (state === 'error') {
                statusBadge.textContent = 'Error';
                statusBadge.className = 'badge error';
                downloadStatusRegion.textContent = details.message || 'Conversion failed. See diagnostic details below.';
                downloadStatusRegion.classList.remove('hidden');
                downloadLinks.classList.add('hidden');
            }
        } else if (section === 'compile') {
            if (state === 'no_file') {
                compileStatusRegion.textContent = 'No file uploaded.';
                compileStatusRegion.classList.remove('hidden');
                compileLog.classList.add('hidden');
            } else if (state === 'awaiting') {
                compileStatusRegion.textContent = 'Awaiting translation.';
                compileStatusRegion.classList.remove('hidden');
                compileLog.classList.add('hidden');
            } else if (state === 'in_progress') {
                compileStatusRegion.textContent = 'Compilation in progress...';
                compileStatusRegion.classList.remove('hidden');
                compileLog.classList.add('hidden');
            } else if (state === 'not_applicable') {
                compileStatusRegion.textContent = 'Compilation not applicable for the selected target format.';
                compileStatusRegion.classList.remove('hidden');
                compileLog.classList.add('hidden');
            } else if (state === 'success') {
                compileStatusRegion.textContent = 'Compilation succeeded cleanly.';
                compileStatusRegion.classList.remove('hidden');
                compileLog.classList.add('hidden');
            } else if (state === 'present') {
                compileStatusRegion.textContent = 'Compilation failed. View log details below.';
                compileStatusRegion.classList.remove('hidden');
                compileLog.classList.remove('hidden');
            } else if (state === 'error') {
                compileStatusRegion.textContent = 'Error occurred during compilation.';
                compileStatusRegion.classList.remove('hidden');
                compileLog.classList.remove('hidden');
            }
        }
    }

    // Handle drag and drop styling
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
        }, false);
    });

    // Handle dropped files
    uploadZone.addEventListener('drop', (e) => {
        if (fileInput.disabled) {
            return;
        }
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelected(files[0]);
        }
    });

    // Handle selected files
    fileInput.addEventListener('change', (e) => {
        if (fileInput.files.length > 0) {
            handleFileSelected(fileInput.files[0]);
        }
    });

    // Update form options visibility when target format is changed
    targetFormatSelect.addEventListener('change', () => {
        updateOptionVisibility();
    });

    function handleFileSelected(file) {
        fileNameDisplay.textContent = file.name;
        
        // Auto-detect input type by extension and update defaults
        const ext = file.name.split('.').pop().toLowerCase();
        
        if (ext === 'brf' || ext === 'brl') {
            // Braille input -> usually want LilyPond output
            targetFormatSelect.value = 'lilypond';
        } else if (ext === 'ly' || ext === 'musicxml' || ext === 'xml' || ext === 'mxl') {
            // Sheet music input -> usually want Braille output
            targetFormatSelect.value = 'braille';
        }
        
        updateOptionVisibility(ext);
        announceStatus(`Selected file: ${file.name}`);

        // Reset output states to awaiting
        updateSectionState('validation', 'awaiting');
        updateSectionState('downloads', 'awaiting');
        updateSectionState('compile', 'awaiting');
    }

    function updateOptionVisibility(fileExt) {
        const target = targetFormatSelect.value;
        const ext = fileExt || (fileInput.files[0] ? fileInput.files[0].name.split('.').pop().toLowerCase() : '');

        // Show/hide category: Only relevant when input is Braille or output is LilyPond
        if (ext === 'brf' || ext === 'brl' || target === 'lilypond') {
            groupCategory.classList.remove('hidden');
        } else {
            groupCategory.classList.add('hidden');
        }

        // Show/hide compression, page-number pagination, measure-numbering
        // mode, octave-every-measure, and repeat-sign settings: only
        // relevant when output is Braille (these are all braille-specific
        // concepts, meaningless for LilyPond/MusicXML).
        if (target === 'braille' || target === 'brl') {
            groupCompression.classList.remove('hidden');
            groupPageNumbers.classList.remove('hidden');
            groupMeasureNumbering.classList.remove('hidden');
            groupOctaveEveryMeasure.classList.remove('hidden');
            groupIncludeClefSign.classList.remove('hidden');
            groupFullMeasureRepeat.classList.remove('hidden');
            groupMinRepeatedMeasures.classList.remove('hidden');
        } else {
            groupCompression.classList.add('hidden');
            groupPageNumbers.classList.add('hidden');
            groupMeasureNumbering.classList.add('hidden');
            groupOctaveEveryMeasure.classList.add('hidden');
            groupIncludeClefSign.classList.add('hidden');
            groupFullMeasureRepeat.classList.add('hidden');
            groupMinRepeatedMeasures.classList.add('hidden');
        }
    }

    function announceStatus(text, priority = 'polite') {
        statusAnnouncer.setAttribute('aria-live', priority);
        statusAnnouncer.textContent = text;
    }

    // FastAPI's own 4xx responses (e.g. HTTPException) send `detail` as a
    // plain string, but its automatic request-validation errors (422, e.g.
    // a missing required field) send `detail` as an array of
    // {type, loc, msg} objects instead. Handle both so the UI never shows
    // a raw "[object Object]".
    function formatErrorDetail(detail) {
        if (typeof detail === 'string') {
            return detail;
        }
        if (Array.isArray(detail)) {
            return detail
                .map(item => {
                    if (item && typeof item === 'object') {
                        const field = Array.isArray(item.loc) ? item.loc.join('.') : '';
                        return field ? `${field}: ${item.msg}` : item.msg;
                    }
                    return String(item);
                })
                .join('\n');
        }
        if (detail && typeof detail === 'object') {
            return JSON.stringify(detail);
        }
        return 'An unknown error occurred during conversion.';
    }

    // Disable/enable the file picker and submit button together, so a
    // translation in progress can't be interrupted by picking a new file
    // or double-submitting.
    function setBusy(isBusy) {
        submitBtn.disabled = isBusy;
        fileInput.disabled = isBusy;
        uploadZone.classList.toggle('disabled', isBusy);
        submitBtnLabel.textContent = isBusy ? 'Translating...' : 'Translate Score';
    }

    function setProgress(percent, label, indeterminate) {
        progressContainer.classList.remove('hidden');
        progressTrack.classList.toggle('indeterminate', !!indeterminate);
        progressTrack.setAttribute('aria-valuenow', indeterminate ? '' : String(percent));
        progressFill.style.width = `${percent}%`;
        progressLabel.textContent = label;
    }

    function hideProgress() {
        progressContainer.classList.add('hidden');
        progressTrack.classList.remove('indeterminate');
        progressFill.style.width = '0%';
    }

    // Initialize option visibility and empty states
    updateOptionVisibility();
    updateSectionState('validation', 'no_file');
    updateSectionState('downloads', 'no_file');
    updateSectionState('compile', 'no_file');

    // Form Submission
    form.addEventListener('submit', (e) => {
        e.preventDefault();

        if (fileInput.files.length === 0) {
            alert('Please select a file to translate.');
            return;
        }

        // Snapshot the form data before disabling any controls -- FormData
        // silently omits disabled form fields, so building this after
        // setBusy(true) would drop the file field entirely.
        const formData = new FormData(form);

        // FormData also omits an unchecked checkbox entirely (not "false",
        // just absent) -- the backend's Form(True) default for
        // page_numbers would then silently override an explicit uncheck
        // back to true. Set it explicitly either way so unchecking it
        // actually turns pagination off.
        formData.set('page_numbers', pageNumbersCheckbox.checked ? 'true' : 'false');

        // Set Loading States
        setBusy(true);
        setProgress(0, 'Uploading: 0%', false);
        announceStatus('Uploading and translating score. Please wait...', 'assertive');

        // Transition states to in_progress
        updateSectionState('validation', 'in_progress');
        updateSectionState('downloads', 'in_progress');
        updateSectionState('compile', 'in_progress');

        downloadLinks.innerHTML = '';
        validationTbody.innerHTML = '';
        compileLog.textContent = '';

        // XMLHttpRequest (not fetch) is used here specifically because it's
        // the only option that exposes upload progress events -- fetch has
        // no equivalent for a multipart body.
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/convert');

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                setProgress(percent, `Uploading: ${percent}%`, false);
            }
        });

        xhr.upload.addEventListener('load', () => {
            // Upload finished; the server is now parsing, validating, and
            // (for LilyPond output) compiling the score. There's no
            // progress signal for that phase, so switch to an
            // indeterminate indicator rather than a fake percentage.
            setProgress(100, 'Processing score...', true);
            announceStatus('Upload complete. Processing score...', 'polite');
        });

        xhr.addEventListener('load', () => {
            setBusy(false);
            hideProgress();

            let data;
            try {
                data = JSON.parse(xhr.responseText);
            } catch (parseErr) {
                showError('The server returned an unexpected response.');
                return;
            }

            if (xhr.status < 200 || xhr.status >= 300) {
                showError(formatErrorDetail(data.detail));
                return;
            }

            showResults(data);
        });

        xhr.addEventListener('error', () => {
            setBusy(false);
            hideProgress();
            showError('Network/connection error: could not reach the server.');
        });

        xhr.send(formData);
    });

    function showError(message) {
        updateSectionState('downloads', 'error', { message: 'Conversion failed. See diagnostic details below.' });
        updateSectionState('compile', 'error');
        updateSectionState('validation', 'no_file');
        
        compileLog.textContent = message;
        announceStatus(`Conversion failed. Error details: ${message}`, 'assertive');
    }

    function showResults(data) {
        // 1. Compile status check and state transitions
        let badgeText = 'Success';
        let badgeClass = 'success';
        let compileState = 'not_applicable';
        let announceText = 'Score translated successfully! Download links are ready below.';

        if (data.target_format === 'lilypond') {
            if (data.compile_success === false) {
                badgeText = 'Conversion Success (Compile Failed)';
                badgeClass = 'warning';
                compileState = 'present';
                compileLog.textContent = data.compile_error || 'LilyPond compilation failed.';
                announceText = 'Score converted successfully to LilyPond, but PDF/MIDI compilation failed.';
            } else {
                compileState = 'success';
            }
        }
        
        // Update compile section state
        updateSectionState('compile', compileState);
        
        // 2. Download Buttons
        downloadLinks.innerHTML = '';
        const files = data.files || {};
        const fileKeys = Object.keys(files);
        
        if (fileKeys.length > 0) {
            const buttonInfo = {
                'ly': { text: '🎼 LilyPond Source', title: 'Download LilyPond score source file' },
                'pdf': { text: '📄 PDF Sheet Music', title: 'Download compiled PDF sheet music' },
                'midi': { text: '🎵 MIDI Audio', title: 'Download compiled MIDI audio file' },
                'brf': { text: '⠃ BANA Braille (BRF)', title: 'Download formatted ASCII braille music file' },
                'brl': { text: '⠃ BANA Braille (BRL)', title: 'Download formatted Unicode braille music file' },
                'musicxml': { text: '🎼 MusicXML File', title: 'Download sheet music in MusicXML format' }
            };

            for (const [key, url] of Object.entries(files)) {
                const info = buttonInfo[key] || { text: `Download ${key.toUpperCase()}`, title: 'Download file' };
                const link = document.createElement('a');
                link.href = url;
                link.className = 'download-btn';
                link.textContent = info.text;
                link.title = info.title;
                link.setAttribute('aria-label', info.title);
                downloadLinks.appendChild(link);
            }
            
            updateSectionState('downloads', 'present', { badgeText: badgeText, badgeClass: badgeClass });
        } else {
            updateSectionState('downloads', 'empty');
        }
        
        announceStatus(announceText, 'polite');

        // 3. Validation Report
        validationTbody.innerHTML = '';
        if (data.validation_report && data.validation_report.length > 0) {
            data.validation_report.forEach(c => {
                const tr = document.createElement('tr');
                
                // Reference
                const tdRef = document.createElement('td');
                let ref = '';
                if (c.line_number > 0) ref += `L${c.line_number} `;
                if (c.measure_number > 0) ref += `M${c.measure_number}`;
                tdRef.textContent = ref || '-';
                tr.appendChild(tdRef);

                // Rule ID
                const tdRule = document.createElement('td');
                tdRule.textContent = c.rule_id;
                tr.appendChild(tdRule);

                // Severity
                const tdSeverity = document.createElement('td');
                const badge = document.createElement('span');
                badge.className = `table-badge ${c.severity.toLowerCase()}`;
                badge.textContent = c.severity;
                tdSeverity.appendChild(badge);
                tr.appendChild(tdSeverity);

                // Message
                const tdMsg = document.createElement('td');
                tdMsg.textContent = c.message;
                tr.appendChild(tdMsg);

                // Suggestions
                const tdSug = document.createElement('td');
                if (c.proposed_fix) {
                    tdSug.textContent = c.proposed_fix;
                } else {
                    tdSug.textContent = '-';
                }
                tr.appendChild(tdSug);

                validationTbody.appendChild(tr);
            });
            
            updateSectionState('validation', 'present', { count: data.validation_report.length });
        } else {
            updateSectionState('validation', 'empty');
        }
    }
});
