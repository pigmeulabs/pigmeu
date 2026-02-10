// ===== DOM Elements =====
const navLinks = document.querySelectorAll('.nav-link');
const sections = document.querySelectorAll('.section');
const modal = document.getElementById('task-modal');
const modalClose = document.querySelector('.modal-close');

// Forms
const submitForm = document.getElementById('submit-form');
const submitResult = document.getElementById('submit-result');
const credForm = document.getElementById('cred-form');
const credResult = document.getElementById('cred-result');
const credList = document.getElementById('cred-list');
const promptForm = document.getElementById('prompt-form');
const promptResult = document.getElementById('prompt-result');
const promptList = document.getElementById('prompt-list');

// Tasks section
const refreshBtn = document.getElementById('refresh-tasks');
const prevBtn = document.getElementById('prev-page');
const nextBtn = document.getElementById('next-page');
const paginationInfo = document.getElementById('tasks-pagination');
const tasksGrid = document.getElementById('tasks-grid');

let skip = 0;
const limit = 10;
let currentTaskId = null;

// ===== Navigation =====
function showSection(sectionId) {
  sections.forEach(s => s.classList.remove('active'));
  document.getElementById(sectionId)?.classList.add('active');
  
  navLinks.forEach(link => {
    link.classList.remove('active');
    if (link.dataset.section === sectionId) {
      link.classList.add('active');
    }
  });
  
  // Update page title
  const titleMap = {
    'tasks-section': 'Tasks Dashboard',
    'submit-section': 'New Submission',
    'settings-section': 'Settings'
  };
  document.querySelector('.header-left h1').textContent = titleMap[sectionId] || 'Dashboard';
}

navLinks.forEach(link => {
  link.addEventListener('click', (e) => {
    e.preventDefault();
    const section = link.dataset.section;
    showSection(section);
  });
});

// ===== Modal Management =====
function openModal() {
  modal.classList.add('active');
}

function closeModal() {
  modal.classList.remove('active');
  currentTaskId = null;
}

modalClose.addEventListener('click', closeModal);
modal.addEventListener('click', (e) => {
  if (e.target === modal) closeModal();
});

// ===== Tasks Management =====
async function fetchTasks() {
  tasksGrid.innerHTML = '<div class="loading">Loading tasks...</div>';
  try {
    const res = await fetch(`/tasks?skip=${skip}&limit=${limit}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to fetch');
    
    tasksGrid.innerHTML = '';
    if (!data.tasks || data.tasks.length === 0) {
      tasksGrid.innerHTML = '<div class="loading">No tasks found</div>';
    } else {
      data.tasks.forEach(t => {
        const card = document.createElement('div');
        card.className = 'task-card';
        card.innerHTML = `
          <h3>${t.title}</h3>
          <p><strong>${t.author_name}</strong></p>
          <p class="text-muted">${t.amazon_url.substring(0, 50)}...</p>
          <span class="task-status status-${t.status.toLowerCase()}">${t.status}</span>
        `;
        card.addEventListener('click', () => {
          currentTaskId = t.id;
          fetchTaskDetails(t.id);
          openModal();
        });
        tasksGrid.appendChild(card);
      });
    }

    const start = data.skip + 1;
    const end = data.skip + data.count;
    paginationInfo.textContent = `Showing ${start}-${end} of ${data.total}`;
    prevBtn.disabled = data.skip <= 0;
    nextBtn.disabled = data.skip + data.count >= data.total;
  } catch (err) {
    tasksGrid.innerHTML = `<div class="loading">Error: ${err.message}</div>`;
    paginationInfo.textContent = '';
  }
}

async function fetchTaskDetails(id) {
  const modalContent = document.querySelector('.modal-content');
  modalContent.innerHTML = '<div style="padding:20px;">Loading details...</div>';
  
  try {
    const res = await fetch(`/tasks/${id}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to fetch details');
    
    const sub = data.submission;
    let html = `<h3>${sub.title}</h3>`;
    html += `<p><strong>Author:</strong> <span id="task-author">${sub.author_name}</span></p>`;
    html += `<p><strong>Status:</strong> <span id="task-status" class="task-status status-${sub.status.toLowerCase()}">${sub.status}</span></p>`;
    html += `<p><strong>URL:</strong> <a href="${sub.amazon_url}" target="_blank">View on Amazon</a></p>`;
    
    // Progress steps
    html += `<div style="margin:16px 0;"><h4 style="margin-bottom:8px;">Progress</h4>`;
    data.progress.steps.forEach(s => {
      html += `<div style="padding:4px 0;">${s.completed ? '✅' : '⭕'} ${s.label}</div>`;
    });
    html += `</div>`;
    
    // Action buttons
    html += `
      <div style="margin:16px 0; display:flex; gap:8px;">
        <button id="edit-task" class="btn btn-secondary">Edit</button>
        <button id="generate-context" class="btn btn-secondary">Generate Context</button>
        <button id="generate-article" class="btn btn-secondary">Generate Article</button>
      </div>
    `;
    
    // Extracted data
    if (data.book) {
      html += `<h4>Extracted Data</h4><pre style="background:#f5f5f5;padding:8px;border-radius:4px;overflow-x:auto;font-size:12px;">${JSON.stringify(data.book.extracted, null, 2)}</pre>`;
    }
    
    // Edit form (hidden)
    html += `
      <form id="task-edit-form" style="display:none;margin-top:16px;">
        <div class="form-group">
          <label class="form-label">Title</label>
          <input class="form-input" name="title" id="edit-title">
        </div>
        <div class="form-group">
          <label class="form-label">Author</label>
          <input class="form-input" name="author_name" id="edit-author">
        </div>
        <div class="form-group">
          <label class="form-label">Extracted JSON</label>
          <textarea class="form-textarea" id="edit-extracted"></textarea>
        </div>
        <button type="submit" class="btn btn-primary">Save Changes</button>
        <button id="cancel-edit" type="button" class="btn btn-secondary">Cancel</button>
      </form>
    `;
    
    modalContent.innerHTML = html;

    // Wire up buttons
    document.getElementById('edit-task').addEventListener('click', () => {
      document.getElementById('task-edit-form').style.display = 'block';
      document.getElementById('edit-title').value = sub.title || '';
      document.getElementById('edit-author').value = sub.author_name || '';
      document.getElementById('edit-extracted').value = JSON.stringify((data.book && data.book.extracted) || {}, null, 2);
    });

    document.getElementById('cancel-edit').addEventListener('click', () => {
      document.getElementById('task-edit-form').style.display = 'none';
    });

    document.getElementById('task-edit-form').addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const payload = {
        submission: {
          title: document.getElementById('edit-title').value,
          author_name: document.getElementById('edit-author').value,
        },
        book: {
          extracted: JSON.parse(document.getElementById('edit-extracted').value || '{}')
        }
      };
      try {
        const res = await fetch(`/tasks/${id}`, {
          method: 'PATCH',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify(payload)
        });
        const r = await res.json();
        if (!res.ok) throw new Error(r.detail || 'Failed to save');
        fetchTaskDetails(id);
      } catch (err) {
        alert('Error saving: ' + err.message);
      }
    });

    document.getElementById('generate-context').addEventListener('click', async () => {
      try {
        const res = await fetch(`/tasks/${id}/generate_context`, { method: 'POST' });
        const r = await res.json();
        if (!res.ok) throw new Error(r.detail || 'Failed');
        alert('Context generation enqueued');
        setTimeout(() => fetchTaskDetails(id), 2000);
      } catch (err) {
        alert('Error: ' + err.message);
      }
    });

    document.getElementById('generate-article').addEventListener('click', async () => {
      try {
        const res = await fetch(`/tasks/${id}/generate_article`, { method: 'POST' });
        const r = await res.json();
        if (!res.ok) throw new Error(r.detail || 'Failed');
        alert('Article generation enqueued');
        setTimeout(() => fetchTaskDetails(id), 2000);
      } catch (err) {
        alert('Error: ' + err.message);
      }
    });
  } catch (err) {
    modalContent.innerHTML = `<div style="padding:20px;"><p class="error">Error: ${err.message}</p></div>`;
  }
}

// ===== Submission Form =====
submitForm.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  submitResult.textContent = 'Submitting...';
  submitResult.className = '';
  
  const formData = new FormData(submitForm);
  const body = Object.fromEntries(formData.entries());
  
  // Validation
  if (!body.title || !body.author_name || !body.amazon_url) {
    submitResult.textContent = 'Please fill in all required fields.';
    submitResult.className = 'form-result error';
    return;
  }
  if (!/^https?:\/\//i.test(body.amazon_url)) {
    submitResult.textContent = 'Amazon URL must start with http:// or https://';
    submitResult.className = 'form-result error';
    return;
  }

  try {
    const res = await fetch('/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Submission failed');
    submitResult.textContent = `✓ Submitted! Task ID: ${data.id}`;
    submitResult.className = 'form-result success';
    submitForm.reset();
    setTimeout(() => { skip = 0; fetchTasks(); }, 1000);
  } catch (err) {
    submitResult.textContent = `✗ Error: ${err.message}`;
    submitResult.className = 'form-result error';
  }
});

// ===== Pagination =====
refreshBtn.addEventListener('click', () => { skip = 0; fetchTasks(); });
prevBtn.addEventListener('click', () => { skip = Math.max(0, skip - limit); fetchTasks(); });
nextBtn.addEventListener('click', () => { skip = skip + limit; fetchTasks(); });

// ===== Credentials Management =====
async function fetchCredentials() {
  credList.innerHTML = '<li class="loading">Loading...</li>';
  try {
    const res = await fetch('/settings/credentials');
    const items = await res.json();
    credList.innerHTML = '';
    if (items.length === 0) {
      credList.innerHTML = '<li class="empty-state">No credentials saved yet</li>';
    } else {
      items.forEach(c => {
        const li = document.createElement('li');
        li.innerHTML = `
          <span><strong>${c.service}</strong>: ${c.key}</span>
          <button class="btn btn-secondary" style="padding:4px 8px;font-size:12px;">Delete</button>
        `;
        li.querySelector('button').addEventListener('click', async () => {
          if (!confirm('Delete this credential?')) return;
          const res = await fetch(`/settings/credentials/${c._id}`, { method: 'DELETE' });
          if (res.ok) {
            fetchCredentials();
          } else {
            alert('Delete failed');
          }
        });
        credList.appendChild(li);
      });
    }
  } catch (err) {
    credList.innerHTML = `<li class="empty-state">Error: ${err.message}</li>`;
  }
}

credForm.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  credResult.textContent = 'Saving...';
  credResult.className = '';
  
  const form = new FormData(credForm);
  const body = Object.fromEntries(form.entries());
  body.encrypted = form.get('encrypted') === 'on';
  
  try {
    const res = await fetch('/settings/credentials', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed');
    credResult.textContent = `✓ Credential saved: ${data.id}`;
    credResult.className = 'form-result success';
    credForm.reset();
    fetchCredentials();
  } catch (err) {
    credResult.textContent = `✗ Error: ${err.message}`;
    credResult.className = 'form-result error';
  }
});

// ===== Prompts Management =====
async function fetchPrompts() {
  promptList.innerHTML = '<li class="loading">Loading...</li>';
  try {
    const res = await fetch('/settings/prompts');
    const items = await res.json();
    promptList.innerHTML = '';
    if (items.length === 0) {
      promptList.innerHTML = '<li class="empty-state">No prompts saved yet</li>';
    } else {
      items.forEach(p => {
        const li = document.createElement('li');
        li.innerHTML = `
          <div>
            <strong>${p.name}</strong> — ${p.purpose || 'No description'}
            <br><small style="color:#999;">${p.system_prompt.substring(0, 100)}...</small>
          </div>
          <button class="btn btn-secondary" style="padding:4px 8px;font-size:12px;">Delete</button>
        `;
        li.querySelector('button').addEventListener('click', async () => {
          if (!confirm('Delete this prompt?')) return;
          const res = await fetch(`/settings/prompts/${p.id}`, { method: 'DELETE' });
          if (res.ok) {
            fetchPrompts();
          } else {
            alert('Delete failed');
          }
        });
        promptList.appendChild(li);
      });
    }
  } catch (err) {
    promptList.innerHTML = `<li class="empty-state">Error: ${err.message}</li>`;
  }
}

promptForm.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  promptResult.textContent = 'Saving...';
  promptResult.className = '';
  
  const form = new FormData(promptForm);
  const body = Object.fromEntries(form.entries());
  body.temperature = parseFloat(body.temperature || 0.7);
  body.max_tokens = parseInt(body.max_tokens || 800, 10);
  
  try {
    const res = await fetch('/settings/prompts', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed');
    promptResult.textContent = `✓ Prompt saved: ${data.id}`;
    promptResult.className = 'form-result success';
    promptForm.reset();
    fetchPrompts();
  } catch (err) {
    promptResult.textContent = `✗ Error: ${err.message}`;
    promptResult.className = 'form-result error';
  }
});

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', () => {
  showSection('tasks-section');
  fetchTasks();
  fetchCredentials();
  fetchPrompts();
});
