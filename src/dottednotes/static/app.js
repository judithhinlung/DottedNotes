document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('convert-form');
    const fileInput = document.getElementById('music-file');
    const uploadZone = document.getElementById('upload-zone');
    const fileNameDisplay = document.getElementById('file-name-display');
    const targetFormatSelect = document.getElementById('target_format');
    const submitBtn = document.getElementById('submit-btn');
    const btnSpinner = document.getElementById('btn-spinner');
    const statusAnnouncer = document.getElementById('status-announcement');

    // UI Option Groups
    const groupCategory = document.getElementById('group-category');
    const groupCompression = document.getElementById('group-compression');

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

        // Show/hide compression: Only relevant when output is Braille
        if (target === 'braille') {
            groupCompression.classList.remove('hidden');
        } else {
            groupCompression.classList.add('hidden');
        }
    }

    function announceStatus(text, priority = 'polite') {
        statusAnnouncer.setAttribute('aria-live', priority);
        statusAnnouncer.textContent = text;
    }

    // Initialize option visibility
    updateOptionVisibility();

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (fileInput.files.length === 0) {
            alert('Please select a file to translate.');
            return;
        }

        // Set Loading States
        submitBtn.disabled = true;
        btnSpinner.classList.remove('sr-only');
        announceStatus('Uploading and translating score. Please wait...', 'assertive');

        // Hide old results
        resultSection.classList.add('hidden');
        validationSection.classList.add('hidden');
        compileLogContainer.classList.add('hidden');
        downloadLinks.innerHTML = '';
        validationTbody.innerHTML = '';

        const formData = new FormData(form);

        try {
            const response = await fetch('/api/convert', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            // Clear Loading States
            submitBtn.disabled = false;
            btnSpinner.classList.add('sr-only');

            if (!response.ok) {
                const errMsg = data.detail || 'An unknown error occurred during conversion.';
                showError(errMsg);
                return;
            }

            // Render Success results
            showResults(data);

        } catch (error) {
            submitBtn.disabled = false;
            btnSpinner.classList.add('sr-only');
            showError(`Network/connection error: ${error.message}`);
        }
    });

    function showError(message) {
        resultSection.classList.remove('hidden');
        statusBadge.textContent = 'Error';
        statusBadge.className = 'badge error';
        
        downloadLinks.innerHTML = '<p class="error-text">Conversion failed. See diagnostic details below.</p>';
        
        compileLogContainer.classList.remove('hidden');
        compileLog.textContent = message;
        
        announceStatus(`Conversion failed. Error details: ${message}`, 'assertive');
    }

    function showResults(data) {
        resultSection.classList.remove('hidden');

        // 1. Compile status check
        if (data.target_format === 'lilypond' && data.compile_success === false) {
            statusBadge.textContent = 'Conversion Success (Compile Failed)';
            statusBadge.className = 'badge warning';
            
            compileLogContainer.classList.remove('hidden');
            compileLog.textContent = data.compile_error || 'LilyPond compilation failed.';
            announceStatus('Score converted successfully to LilyPond, but PDF/MIDI compilation failed.', 'polite');
        } else {
            statusBadge.textContent = 'Success';
            statusBadge.className = 'badge success';
            announceStatus('Score translated successfully! Download links are ready below.', 'polite');
        }

        // 2. Download Buttons
        const buttonInfo = {
            'ly': { text: '🎼 LilyPond Source', title: 'Download LilyPond score source file' },
            'pdf': { text: '📄 PDF Sheet Music', title: 'Download compiled PDF sheet music' },
            'midi': { text: '🎵 MIDI Audio', title: 'Download compiled MIDI audio file' },
            'brf': { text: '⠃ BANA Braille (BRF)', title: 'Download formatted braille music file' },
            'musicxml': { text: '🎼 MusicXML File', title: 'Download sheet music in MusicXML format' }
        };

        for (const [key, url] of Object.entries(data.files)) {
            const info = buttonInfo[key] || { text: `Download ${key.toUpperCase()}`, title: 'Download file' };
            const link = document.createElement('a');
            link.href = url;
            link.className = 'download-btn';
            link.textContent = info.text;
            link.title = info.title;
            link.setAttribute('aria-label', info.title);
            downloadLinks.appendChild(link);
        }

        // 3. Validation Report
        if (data.validation_report && data.validation_report.length > 0) {
            validationSection.classList.remove('hidden');
            validationSummary.textContent = `Found ${data.validation_report.length} BANA formatting rule violation(s). Review recommendations below.`;

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
        }
    }
});
