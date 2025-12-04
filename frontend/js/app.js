const RAW_BASE_URL = (window.APP_CONFIG && window.APP_CONFIG.apiBaseUrl) || '';
const API_BASE = RAW_BASE_URL.endsWith('/') ? RAW_BASE_URL.slice(0, -1) : RAW_BASE_URL;
let recentUploads = [];

document.addEventListener('DOMContentLoaded', () => {
  initializeApp();
});

function initializeApp() {
  initFileUpload();
  loadRecentUploads();

  document.getElementById('search-input').addEventListener('keypress', e => {
    if (e.key === 'Enter') searchDocuments();
  });

  document.getElementById('document-id-input').addEventListener('keypress', e => {
    if (e.key === 'Enter') checkStatus();
  });
}

function requireApiUrl() {
  if (!API_BASE) throw new Error('API base URL missing (config.js not loaded).');
}

function showTab(tabName, event) {
  document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
  document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
  document.getElementById(`${tabName}-tab`).classList.add('active');
  event.target.classList.add('active');
}

// --- Upload ---
function initFileUpload() {
  const uploadArea = document.getElementById('upload-area');
  const fileInput = document.getElementById('file-input');
  const selectBtn = document.getElementById('select-file-btn');

  selectBtn.addEventListener('click', e => {
    e.stopPropagation();
    fileInput.click();
  });

  uploadArea.addEventListener('click', e => {
    if (e.target !== selectBtn && !selectBtn.contains(e.target)) fileInput.click();
  });

  fileInput.addEventListener('change', e => {
    const file = e.target.files[0];
    if (file) {
      uploadFile(file);
      e.target.value = '';
    }
  });

  uploadArea.addEventListener('dragover', e => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
  });
  uploadArea.addEventListener('dragleave', e => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
  });
  uploadArea.addEventListener('drop', e => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  });
}

async function uploadFile(file) {
  try {
    requireApiUrl();
    toggleProgress(true, 'Converting file...');
    const base64File = await fileToBase64(file);

    toggleProgress(true, 'Uploading to API...');
    const response = await fetch(`${API_BASE}/documents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: file.name, base64File })
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Upload failed (${response.status}): ${text}`);
    }

    const data = await response.json();
    showUploadResult(true, `
      <h3>✅ Upload Successful!</h3>
      <p><strong>Document ID:</strong> ${data.documentId}</p>
      <p><strong>Filename:</strong> ${file.name}</p>
      <p>Processing started. Track it in the "Check Status" tab.</p>
    `);

    document.getElementById('document-id-input').value = data.documentId || '';
    addToRecentUploads({ documentId: data.documentId, filename: file.name, uploadTime: new Date().toLocaleString('en-US') });
  } catch (err) {
    console.error('Upload error:', err);
    showUploadResult(false, `
      <h3>❌ Upload Failed</h3>
      <p>${err.message}</p>
    `);
  } finally {
    toggleProgress(false);
  }
}

function toggleProgress(show, text = '') {
  const bar = document.getElementById('upload-progress');
  const fill = document.getElementById('progress-fill');
  const label = document.getElementById('progress-text');
  if (show) {
    bar.style.display = 'block';
    label.textContent = text;
    fill.style.width = text.includes('Uploading') ? '80%' : '30%';
  } else {
    bar.style.display = 'none';
    fill.style.width = '0%';
    label.textContent = '';
  }
}

function showUploadResult(success, html) {
  const box = document.getElementById('upload-result');
  box.innerHTML = html;
  box.className = 'result-box ' + (success ? 'success' : 'error');
  box.style.display = 'block';
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.onerror = () => reject(new Error('File reading failed'));
    reader.readAsDataURL(file);
  });
}

function addToRecentUploads(upload) {
  recentUploads.unshift(upload);
  recentUploads = recentUploads.slice(0, 5);
  localStorage.setItem('recentUploads', JSON.stringify(recentUploads));
  displayRecentUploads();
}

function loadRecentUploads() {
  const saved = localStorage.getItem('recentUploads');
  if (saved) {
    recentUploads = JSON.parse(saved);
    displayRecentUploads();
  }
}

function displayRecentUploads() {
  const container = document.getElementById('recent-uploads');
  if (!recentUploads.length) {
    container.innerHTML = '<p class="text-muted">No upload history</p>';
    return;
  }
  container.innerHTML = recentUploads
    .map(upload => `
      <div class="document-item" onclick="viewDocumentStatus('${upload.documentId}')">
        <div class="document-title">📄 ${upload.filename}</div>
        <div class="document-meta">
          <span>ID: ${upload.documentId.substring(0, 8)}...</span>
          <span>Upload Time: ${upload.uploadTime}</span>
        </div>
      </div>
    `)
    .join('');
}

function viewDocumentStatus(id) {
  document.getElementById('document-id-input').value = id;
  document.querySelectorAll('.tab-button')[2].click();
  checkStatus();
}

// --- Search ---
async function searchDocuments() {
  try {
    requireApiUrl();
    const query = document.getElementById('search-input').value.trim();
    const category = document.getElementById('category-filter').value;
    const type = document.getElementById('type-filter').value;

    document.getElementById('search-results').innerHTML = '<p class="text-muted">Searching...</p>';

    const params = new URLSearchParams();
    if (query) {
      params.append('q', query);
      params.append('query', query);
    }
    if (category) params.append('category', category);
    if (type) params.append('type', type.toLowerCase());
    params.append('limit', '50');

    const response = await fetch(`${API_BASE}/search?${params.toString()}`);
    if (!response.ok) throw new Error('Search request failed');
    const { results = [] } = await response.json();
    displaySearchResults(results);
  } catch (err) {
    document.getElementById('search-results').innerHTML = `<p class="text-muted">Search failed: ${err.message}</p>`;
  }
}

function displaySearchResults(results) {
  const container = document.getElementById('search-results');
  if (!results.length) {
    container.innerHTML = '<p class="text-muted">No matching documents found</p>';
    return;
  }
  container.innerHTML = results
    .map(doc => {
      const fileTypeLabel = resolveFileTypeLabel(doc);
      const docTypeLabel = doc.documentType || 'Unknown document';
      const dateLabel = formatDate(doc.updatedAt || doc.uploadTimestamp);
      const tags = doc.tags || doc.keywords || [];

      return `
        <div class="document-item">
          <div class="document-title">${doc.title || doc.filename}</div>
          <div class="document-meta">
            <span>📁 ${doc.category || 'Uncategorized'}</span>
            <span>📄 ${fileTypeLabel}</span>
            <span>🏷️ ${docTypeLabel}</span>
            <span>📅 ${dateLabel}</span>
          </div>
          <div class="document-summary">${doc.summary || 'Processing summary...'}</div>
          <div class="document-tags">${tags.map(tag => `<span class="tag">${tag}</span>`).join('')}</div>
        </div>
      `;
    })
    .join('');
}

// --- Status ---
async function checkStatus() {
  try {
    requireApiUrl();
    const docId = document.getElementById('document-id-input').value.trim();
    if (!docId) return alert('Please enter document ID');
    document.getElementById('status-result').innerHTML = '<p class="text-muted">Checking...</p>';
    const response = await fetch(`${API_BASE}/status/${docId}`);
    if (!response.ok) throw new Error('Status check failed');
    const data = await response.json();
    displayStatusHistory(data.history || data.statusHistory || []);
  } catch (err) {
    document.getElementById('status-result').innerHTML = `<p class="text-muted">${err.message}</p>`;
  }
}

function displayStatusHistory(history) {
  const container = document.getElementById('status-result');
  if (!history.length) {
    container.innerHTML = '<p class="text-muted">No status records found</p>';
    return;
  }
  const sorted = [...history].sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
  const labels = {
    pending_upload: 'Pending Upload',
    uploaded: 'Uploaded',
    extraction_processing: 'AI Analyzing',
    extraction_completed: 'AI Analysis Completed',
    classification_processing: 'Classifying',
    classification_completed: 'Classified',
    completed: 'Completed',
    failed: 'Failed'
  };
  container.innerHTML = `
    <div class="status-summary">
      <div class="status-item highlight">
        <strong>Current Status: ${labels[sorted[0].status] || sorted[0].status}</strong>
        <p>${sorted[0].message || ''}</p>
        <small>${formatDate(sorted[0].timestamp)}</small>
      </div>
    </div>
    <div class="status-timeline">
      <h4>Status History</h4>
      ${sorted
        .map(item => `
          <div class="status-item">
            <strong>${labels[item.status] || item.status}</strong>
            <p>${item.message || ''}</p>
            <small>${formatDate(item.timestamp)}</small>
          </div>
        `)
        .join('')}
    </div>
  `;
}

// --- Helpers ---
function formatDate(value) {
  if (value === undefined || value === null || value === '') return 'Unknown Date';
  if (typeof value === 'string' && /^\d+$/.test(value)) value = Number(value);
  if (typeof value === 'string' && !isNaN(Date.parse(value))) return new Date(value).toLocaleString('en-US');
  if (typeof value === 'number') return new Date(value * 1000).toLocaleString('en-US');
  return 'Unknown Date';
}

function resolveFileTypeLabel(doc) {
  if (doc.fileType) return doc.fileType.toUpperCase();
  if (doc.filename && doc.filename.includes('.')) {
    return doc.filename.split('.').pop().toUpperCase();
  }
  return 'UNKNOWN';
}
