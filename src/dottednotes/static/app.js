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

    // Post-translation instrument selection (S12-3, BANA Sec. 24
    // single-line format): its braille never states an instrument, so
    // this dialog is shown after translation instead of asked upfront.
    const instrumentDialog = document.getElementById('instrument-dialog');
    const instrumentDialogForm = document.getElementById('instrument-dialog-form');
    const instrumentDialogSelect = document.getElementById('instrument-dialog-select');
    const instrumentDialogContext = document.getElementById('instrument-dialog-context');
    let pendingInstrumentScope = null; // {type: 'main'} or {type: 'part', partIdx, fileKeys}

    // Post-translation key mode selection (S10d-16)
    const keyModeDialog = document.getElementById('key-mode-dialog');
    const keyModeDialogForm = document.getElementById('key-mode-dialog-form');
    const keyModeDialogSelect = document.getElementById('key-mode-dialog-select');
    const keyModeDialogContext = document.getElementById('key-mode-dialog-context');
    const keyModeDialogMajorOption = document.getElementById('key-mode-dialog-major-option');
    const keyModeDialogMinorOption = document.getElementById('key-mode-dialog-minor-option');
    let pendingKeyModeData = null;

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

    // Part selection
    let currentJobId = null;
    let currentParts = []; // [{name, needs_instrument}, ...] from the last showResults()
    const partSelectorContainer = document.getElementById('part-selector-container');
    const partSelector = document.getElementById('part-selector');

    // MIDI Player elements
    const midiPlayerContainer = document.getElementById('midi-player-container');
    const midiPlayer = document.getElementById('midi-player');
    const midiPlayToggle = document.getElementById('midi-play-toggle');
    const midiPlayToggleLabel = document.getElementById('midi-play-toggle-label');

    // Keeps the accessible Play/Pause button in sync with actual
    // <midi-player> playback state. The button is disabled whenever there's
    // no source loaded, so .start()/.stop() (called only from the click
    // handler below) are never reachable with nothing to play.
    function setMidiPlayingState(isPlaying, hasSource = !!midiPlayer.src) {
        midiPlayToggle.setAttribute('aria-pressed', String(isPlaying));
        midiPlayToggleLabel.textContent = isPlaying ? 'Pause' : 'Play';
        midiPlayToggle.disabled = !hasSource;
    }

    midiPlayToggle.addEventListener('click', () => {
        if (midiPlayToggle.getAttribute('aria-pressed') === 'true') {
            midiPlayer.stop();
        } else {
            midiPlayer.start();
        }
    });

    // html-midi-player fires these on both user- and library-driven
    // start/stop (including natural end-of-playback), so listening here
    // keeps the button correct beyond just the click handler above.
    midiPlayer.addEventListener('start', () => setMidiPlayingState(true));
    midiPlayer.addEventListener('stop', () => setMidiPlayingState(false));

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

    function setPartLinkHrefs(jobId, val) {
        const links = downloadLinks.querySelectorAll('.download-btn');
        links.forEach(link => {
            const fileType = link.getAttribute('data-file-type');
            if (val === 'full') {
                link.href = `/api/jobs/${jobId}/${fileType}`;
            } else {
                link.href = `/api/jobs/${jobId}/parts/${val}/${fileType}`;
            }
        });
    }

    // Update link hrefs when part is selected. An extracted piano hand
    // has no real instrument name of its own ("right hand"/"left hand"
    // are parser placeholders, not instruments, S12-3) -- offer the same
    // instrument dialog used post-translation before pointing the
    // download links at it, so the Lilypond/MusicXML exports come out
    // correctly named.
    partSelector.addEventListener('change', () => {
        const val = partSelector.value;
        const jobId = currentJobId;
        if (!jobId) return;

        const part = val !== 'full' ? currentParts[Number(val)] : null;
        if (part && part.needs_instrument) {
            showInstrumentDialog(
                { type: 'part', partIdx: val },
                null,
                `This part ("${part.name}") doesn't have a real instrument name of its own -- pick one for its LilyPond/MusicXML exports.`,
            );
        }
        setPartLinkHrefs(jobId, val);

        // Dynamically update MIDI player source if a source exists
        if (midiPlayer.src) {
            if (val === 'full') {
                midiPlayer.src = `/api/jobs/${jobId}/midi`;
            } else {
                midiPlayer.src = `/api/jobs/${jobId}/parts/${val}/midi`;
            }
            setMidiPlayingState(false);
        }
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

    function populateInstrumentOptions() {
        fetch('/api/instruments')
            .then(res => res.json())
            .then(data => {
                (data.instruments || []).forEach(name => {
                    const option = document.createElement('option');
                    option.value = name;
                    option.textContent = name;
                    instrumentDialogSelect.appendChild(option);
                });
            })
            .catch(() => {
                // Non-fatal -- the dropdown just stays empty; the backend
                // still validates 'instrument' server-side either way.
            });
    }

    // Shows the post-translation instrument dialog (S12-3), pre-selected
    // to `defaultInstrument` if it's one of the dropdown's options.
    // `scope` records what to do when the user confirms -- see
    // instrumentDialogForm's submit handler below.
    function showInstrumentDialog(scope, defaultInstrument, contextText) {
        pendingInstrumentScope = scope;
        instrumentDialogContext.textContent = contextText;
        if (defaultInstrument && [...instrumentDialogSelect.options].some(o => o.value === defaultInstrument)) {
            instrumentDialogSelect.value = defaultInstrument;
        }
        instrumentDialog.showModal();
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
    populateInstrumentOptions();
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

        // Reset MIDI player state
        midiPlayerContainer.classList.add('hidden');
        midiPlayer.src = '';
        setMidiPlayingState(false);

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

        // Reset MIDI player state
        midiPlayerContainer.classList.add('hidden');
        midiPlayer.src = '';
        setMidiPlayingState(false);

        announceStatus(`Conversion failed. Error details: ${message}`, 'assertive');
    }

    function showResults(data) {
        currentJobId = data.job_id;
        currentParts = data.parts || [];

        // Reset and populate part selector
        partSelector.innerHTML = '<option value="full" selected>Full Score (All Parts)</option>';
        if (currentParts.length > 1) {
            currentParts.forEach((part, idx) => {
                const option = document.createElement('option');
                option.value = idx;
                option.textContent = part.name;
                partSelector.appendChild(option);
            });
            partSelectorContainer.classList.remove('hidden');
        } else {
            partSelectorContainer.classList.add('hidden');
        }

        // Auto-load MIDI file if present in the results
        const midiAvailable = !!(data.files && data.files.midi);
        if (midiAvailable) {
            midiPlayer.src = data.files.midi;
            midiPlayerContainer.classList.remove('hidden');
        } else {
            midiPlayerContainer.classList.add('hidden');
            midiPlayer.src = '';
        }
        setMidiPlayingState(false);

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
                if (midiAvailable) {
                    announceText += ' A MIDI player is available for playback.';
                }
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
                link.setAttribute('data-file-type', key);
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

        // 4. Post-translation instrument and key mode confirmation (S12-3, S10d-16)
        if (data.needs_key_mode_selection) {
            pendingKeyModeData = {
                sharps_flats: data.key_signature_sharps_flats,
                major_option: data.major_option,
                minor_option: data.minor_option
            };
        } else {
            pendingKeyModeData = null;
        }

        if (data.needs_instrument_selection) {
            showInstrumentDialog(
                { type: 'main' },
                data.inferred_instrument,
                'This score is in BANA Sec. 24 single-line format, so its braille doesn\'t state which instrument it\'s written for. We\'ve guessed one from the title below -- change it if it\'s wrong.',
            );
        } else if (pendingKeyModeData) {
            showKeyModeDialog(pendingKeyModeData);
        }
    }

    // Handles both the main-score and per-part instrument dialogs (see
    // showInstrumentDialog / pendingInstrumentScope above).
    document.getElementById('instrument-dialog-skip').addEventListener('click', () => {
        instrumentDialog.close();
        if (pendingKeyModeData) {
            showKeyModeDialog(pendingKeyModeData);
        }
    });

    instrumentDialogForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const scope = pendingInstrumentScope;
        const jobId = currentJobId;
        const instrument = instrumentDialogSelect.value;
        if (!scope || !jobId || !instrument) {
            instrumentDialog.close();
            return;
        }

        const confirmBtn = document.getElementById('instrument-dialog-confirm');
        confirmBtn.disabled = true;

        const formData = new FormData();
        formData.set('instrument', instrument);
        const url = scope.type === 'main'
            ? `/api/jobs/${jobId}/instrument`
            : `/api/jobs/${jobId}/parts/${scope.partIdx}/instrument`;

        fetch(url, { method: 'POST', body: formData })
            .then(res => res.json().then(body => ({ ok: res.ok, body })))
            .then(({ ok, body }) => {
                confirmBtn.disabled = false;
                instrumentDialog.close();
                if (!ok) {
                    announceStatus(`Could not set instrument: ${formatErrorDetail(body.detail)}`, 'assertive');
                    return;
                }
                if (scope.type === 'main') {
                    // Re-render the results with the corrected instrument
                    // already applied server-side.
                    showResultsWithoutDialog({
                        ...body,
                        target_format: document.getElementById('target_format').value,
                        parts: currentParts,
                        validation_report: [],
                    });
                    announceStatus(`Instrument set to ${instrument}. Downloads updated.`, 'polite');
                    if (pendingKeyModeData) {
                        showKeyModeDialog(pendingKeyModeData);
                    }
                } else {
                    setPartLinkHrefs(jobId, String(scope.partIdx));
                    announceStatus(`Instrument for this part set to ${instrument}. Downloads updated.`, 'polite');
                }
            })
            .catch(() => {
                confirmBtn.disabled = false;
                instrumentDialog.close();
                announceStatus('Network/connection error: could not set the instrument.', 'assertive');
            });
    });

    // Applies a /api/jobs/{id}/instrument response's updated file links/
    // compile status without re-triggering the instrument dialog itself
    // (showResults would otherwise loop: needs_instrument_selection isn't
    // in this response's shape, so this just re-uses the download/compile
    // rendering half of showResults).
    function showResultsWithoutDialog(data) {
        currentJobId = data.job_id;

        // Keep the MIDI player in sync: setting the instrument can change
        // which MIDI file (if any) the server has compiled for this job.
        if (data.files && data.files.midi) {
            midiPlayer.src = data.files.midi;
            midiPlayerContainer.classList.remove('hidden');
        } else {
            midiPlayerContainer.classList.add('hidden');
            midiPlayer.src = '';
        }
        setMidiPlayingState(false);

        let badgeText = 'Success';
        let badgeClass = 'success';
        let compileState = 'not_applicable';
        if (data.target_format === 'lilypond') {
            if (data.compile_success === false) {
                badgeText = 'Conversion Success (Compile Failed)';
                badgeClass = 'warning';
                compileState = 'present';
                compileLog.textContent = data.compile_error || 'LilyPond compilation failed.';
            } else {
                compileState = 'success';
            }
        }
        updateSectionState('compile', compileState);

        downloadLinks.innerHTML = '';
        const files = data.files || {};
        const buttonInfo = {
            'ly': { text: '🎼 LilyPond Source', title: 'Download LilyPond score source file' },
            'pdf': { text: '📄 PDF Sheet Music', title: 'Download compiled PDF sheet music' },
            'midi': { text: '🎵 MIDI Audio', title: 'Download compiled MIDI audio file' },
            'brf': { text: '⠃ BANA Braille (BRF)', title: 'Download formatted ASCII braille music file' },
            'brl': { text: '⠃ BANA Braille (BRL)', title: 'Download formatted Unicode braille music file' },
            'musicxml': { text: '🎼 MusicXML File', title: 'Download sheet music in MusicXML format' }
        };
        const fileKeys = Object.keys(files);
        if (fileKeys.length > 0) {
            for (const [key, url] of Object.entries(files)) {
                const info = buttonInfo[key] || { text: `Download ${key.toUpperCase()}`, title: 'Download file' };
                const link = document.createElement('a');
                link.href = url;
                link.className = 'download-btn';
                link.setAttribute('data-file-type', key);
                link.textContent = info.text;
                link.title = info.title;
                link.setAttribute('aria-label', info.title);
                downloadLinks.appendChild(link);
            }
            updateSectionState('downloads', 'present', { badgeText, badgeClass });
        } else {
            updateSectionState('downloads', 'empty');
        }
    }

    function showKeyModeDialog(keyModeData) {
        keyModeDialogMajorOption.textContent = keyModeData.major_option;
        keyModeDialogMajorOption.value = 'major';
        keyModeDialogMinorOption.textContent = keyModeData.minor_option;
        keyModeDialogMinorOption.value = 'minor';
        
        const sf = keyModeData.sharps_flats;
        const sfDescription = sf === 0
            ? 'no sharps or flats'
            : `${Math.abs(sf)} ${sf > 0 ? 'sharp' : 'flat'}${Math.abs(sf) > 1 ? 's' : ''}`;
        keyModeDialogContext.textContent = `This braille score contains a key signature (${sfDescription}) but the key mode (major or minor) is ambiguous. Choose whether this is in ${keyModeData.major_option} or its relative minor, ${keyModeData.minor_option}:`;
        
        keyModeDialogSelect.value = 'major'; // default to major
        keyModeDialog.showModal();
    }

    document.getElementById('key-mode-dialog-skip').addEventListener('click', () => {
        keyModeDialog.close();
        pendingKeyModeData = null;
    });

    keyModeDialogForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const jobId = currentJobId;
        const mode = keyModeDialogSelect.value;
        if (!jobId || !mode) {
            keyModeDialog.close();
            pendingKeyModeData = null;
            return;
        }

        const confirmBtn = document.getElementById('key-mode-dialog-confirm');
        confirmBtn.disabled = true;

        const formData = new FormData();
        formData.set('mode', mode);

        fetch(`/api/jobs/${jobId}/key-mode`, { method: 'POST', body: formData })
            .then(res => res.json().then(body => ({ ok: res.ok, body })))
            .then(({ ok, body }) => {
                confirmBtn.disabled = false;
                keyModeDialog.close();
                pendingKeyModeData = null;
                if (!ok) {
                    announceStatus(`Could not set key mode: ${formatErrorDetail(body.detail)}`, 'assertive');
                    return;
                }
                showResultsWithoutDialog({
                    ...body,
                    target_format: document.getElementById('target_format').value,
                    parts: currentParts,
                    validation_report: [],
                });
                const selectedText = mode === 'major' ? keyModeDialogMajorOption.textContent : keyModeDialogMinorOption.textContent;
                announceStatus(`Key mode set to ${selectedText}. Downloads updated.`, 'polite');
            })
            .catch(() => {
                confirmBtn.disabled = false;
                keyModeDialog.close();
                pendingKeyModeData = null;
                announceStatus('Network/connection error: could not set the key mode.', 'assertive');
            });
    });
});
