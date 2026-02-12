const navLinks = document.querySelectorAll('.nav-link');
const sections = document.querySelectorAll('.section');

const modal = document.getElementById('task-modal');
const modalContent = modal ? modal.querySelector('.modal-content') : null;

const submitForm = document.getElementById('submit-form');
const submitResult = document.getElementById('submit-result');

const credForm = document.getElementById('cred-form');
const credResult = document.getElementById('cred-result');
const credList = document.getElementById('cred-list');

const promptForm = document.getElementById('prompt-form');
const promptResult = document.getElementById('prompt-result');
const promptList = document.getElementById('prompt-list');

const refreshBtn = document.getElementById('refresh-tasks');
const prevBtn = document.getElementById('prev-page');
const nextBtn = document.getElementById('next-page');
const paginationInfo = document.getElementById('tasks-pagination');
const tasksGrid = document.getElementById('tasks-grid');
const statsStrip = document.getElementById('stats-strip');
const searchInput = document.getElementById('search-tasks');
const statusFilter = document.getElementById('filter-status');

const runImmediatelyInput = document.getElementById('run_immediately');
const scheduleInput = document.getElementById('schedule_execution');
const addOtherLinkBtn = document.getElementById('add-other-link');
const otherLinksContainer = document.getElementById('other-links-container');

let skip = 0;
const limit = 10;
let currentTaskId = null;
let searchDebounceTimer = null;
let editingCredentialId = null;
let editingPromptId = null;

function safeStringify(value, fallback = '[unserializable object]') {
  try {
    return JSON.stringify(value);
  } catch (_) {
    return fallback;
  }
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function parseApiError(payload, fallback = 'Request failed') {
  const detail = payload?.detail;
  if (!detail) return fallback;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((entry) => {
        if (typeof entry === 'string') return entry;
        if (entry?.msg && Array.isArray(entry?.loc)) {
          return `${entry.loc.join('.')}: ${entry.msg}`;
        }
        return safeStringify(entry);
      })
      .join('; ');
  }
  if (typeof detail === 'object') return safeStringify(detail);
  return String(detail);
}

function normalizeError(err, fallback = 'Unexpected error') {
  if (err instanceof Error && err.message) return err.message;
  if (typeof err === 'string' && err) return err;
  return fallback;
}

function formatDate(value) {
  if (!value) return '-';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return '-';
  return dt.toLocaleString('pt-BR');
}

function statusClass(status) {
  const s = (status || '').toLowerCase();
  if (['published', 'ready_for_review', 'approved'].includes(s)) return 'status-success';
  if (['scraping_failed', 'failed'].includes(s)) return 'status-error';
  if (['context_generated', 'article_generated'].includes(s)) return 'status-info';
  return 'status-warning';
}

function statusLabel(status) {
  const map = {
    pending_scrape: 'Pendente scrape',
    scraping_amazon: 'Scraping Amazon',
    scraping_goodreads: 'Scraping Goodreads',
    context_generation: 'Gerando contexto',
    context_generated: 'Contexto gerado',
    pending_context: 'Pendente contexto',
    pending_article: 'Pendente artigo',
    article_generated: 'Artigo gerado',
    ready_for_review: 'Pronto revisão',
    approved: 'Aprovado',
    published: 'Publicado',
    scraping_failed: 'Falha scrape',
    failed: 'Falha',
  };
  return map[status] || status || '-';
}

function showSection(sectionId) {
  sections.forEach((section) => section.classList.remove('active'));
  document.getElementById(sectionId)?.classList.add('active');

  navLinks.forEach((link) => {
    link.classList.remove('active');
    if (link.dataset.section === sectionId) link.classList.add('active');
  });

  const titleMap = {
    'tasks-section': 'Tasks Dashboard',
    'submit-section': 'New Submission',
    'settings-section': 'Settings',
  };
  const title = document.querySelector('.header-left h1');
  if (title) title.textContent = titleMap[sectionId] || 'Dashboard';
}

navLinks.forEach((link) => {
  link.addEventListener('click', (event) => {
    event.preventDefault();
    showSection(link.dataset.section);
  });
});

function openModal() {
  if (modal) modal.classList.add('active');
}

function closeModal() {
  if (modal) modal.classList.remove('active');
  currentTaskId = null;
}

if (modal) {
  modal.addEventListener('click', (event) => {
    const isClose = event.target.classList?.contains('modal-close');
    if (event.target === modal || isClose) {
      closeModal();
    }
  });
}

function setModalContent(innerHtml) {
  if (!modalContent) return;
  modalContent.innerHTML = `
    <button class="modal-close" type="button" aria-label="Fechar">&times;</button>
    ${innerHtml}
  `;
}

function markdownToHtml(markdown) {
  const lines = String(markdown || '').split('\n');
  let html = '';
  let inList = false;

  lines.forEach((raw) => {
    const line = raw.trim();
    if (!line) {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      return;
    }

    if (line.startsWith('### ')) {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      html += `<h3>${escapeHtml(line.slice(4))}</h3>`;
      return;
    }

    if (line.startsWith('## ')) {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      html += `<h2>${escapeHtml(line.slice(3))}</h2>`;
      return;
    }

    if (line.startsWith('# ')) {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      html += `<h1>${escapeHtml(line.slice(2))}</h1>`;
      return;
    }

    if (line.startsWith('- ')) {
      if (!inList) {
        html += '<ul>';
        inList = true;
      }
      html += `<li>${escapeHtml(line.slice(2))}</li>`;
      return;
    }

    if (inList) {
      html += '</ul>';
      inList = false;
    }

    const paragraph = escapeHtml(line).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html += `<p>${paragraph}</p>`;
  });

  if (inList) html += '</ul>';
  return html;
}

async function fetchStats() {
  if (!statsStrip) return;

  statsStrip.innerHTML = '<div class="loading">Carregando métricas...</div>';
  try {
    const response = await fetch('/stats');
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(data, 'Falha ao carregar métricas'));

    const byStatus = data.by_status || {};
    const published = Number(byStatus.published || 0);
    const review = Number(byStatus.ready_for_review || 0);
    const failed = Number(data.failed_tasks || 0);
    const total = Number(data.total_tasks || 0);
    const successRate = Number(data.success_rate || 0);

    statsStrip.innerHTML = `
      <div class="stat-card">
        <span class="stat-label">Total</span>
        <span class="stat-value">${total}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Publicados</span>
        <span class="stat-value">${published}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Prontos p/ revisão</span>
        <span class="stat-value">${review}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Falhas</span>
        <span class="stat-value">${failed}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Taxa de sucesso</span>
        <span class="stat-value">${(successRate * 100).toFixed(1)}%</span>
      </div>
    `;
  } catch (err) {
    statsStrip.innerHTML = `<div class="loading">Erro: ${escapeHtml(normalizeError(err, 'Falha ao carregar métricas'))}</div>`;
  }
}

function renderTaskCard(task) {
  const card = document.createElement('div');
  card.className = 'task-card';

  const amazonUrl = task.amazon_url ? escapeHtml(task.amazon_url) : '-';
  const shortUrl = amazonUrl.length > 64 ? `${amazonUrl.slice(0, 64)}...` : amazonUrl;

  card.innerHTML = `
    <h3>${escapeHtml(task.title || '-')}</h3>
    <p><strong>${escapeHtml(task.author_name || '-')}</strong></p>
    <p class="text-muted">${shortUrl}</p>
    <div class="task-card-footer">
      <span class="task-status ${statusClass(task.status)}">${escapeHtml(statusLabel(task.status))}</span>
      <span class="text-muted small">${formatDate(task.updated_at)}</span>
    </div>
  `;

  card.addEventListener('click', () => {
    currentTaskId = task.id;
    openModal();
    fetchTaskDetails(task.id);
  });

  return card;
}

async function fetchTasks() {
  if (!tasksGrid) return;

  tasksGrid.innerHTML = '<div class="loading">Carregando tarefas...</div>';

  const params = new URLSearchParams({
    skip: String(skip),
    limit: String(limit),
  });

  const statusValue = statusFilter ? statusFilter.value.trim() : '';
  const searchValue = searchInput ? searchInput.value.trim() : '';

  if (statusValue) params.set('status', statusValue);
  if (searchValue) params.set('search', searchValue);

  try {
    const response = await fetch(`/tasks?${params.toString()}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(data, 'Falha ao carregar tarefas'));

    tasksGrid.innerHTML = '';
    if (!Array.isArray(data.tasks) || data.tasks.length === 0) {
      tasksGrid.innerHTML = '<div class="loading">Nenhuma tarefa encontrada</div>';
    } else {
      data.tasks.forEach((task) => tasksGrid.appendChild(renderTaskCard(task)));
    }

    const total = Number(data.total || 0);
    const count = Number(data.count || 0);
    const start = total > 0 ? Number(data.skip || 0) + 1 : 0;
    const end = total > 0 ? Number(data.skip || 0) + count : 0;

    if (paginationInfo) paginationInfo.textContent = `Mostrando ${start}-${end} de ${total}`;
    if (prevBtn) prevBtn.disabled = Number(data.skip || 0) <= 0;
    if (nextBtn) nextBtn.disabled = Number(data.skip || 0) + count >= total;
  } catch (err) {
    tasksGrid.innerHTML = `<div class="loading">Erro: ${escapeHtml(normalizeError(err, 'Falha ao carregar tarefas'))}</div>`;
    if (paginationInfo) paginationInfo.textContent = '';
  }
}

function renderProgress(steps = []) {
  if (!Array.isArray(steps) || steps.length === 0) return '<p class="text-muted">Sem progresso disponível</p>';

  return `
    <div class="progress-list">
      ${steps
        .map(
          (step) => `
            <div class="progress-item ${step.completed ? 'completed' : ''}">
              <span>${step.completed ? '✅' : '⭕'}</span>
              <span>${escapeHtml(step.label || step.stage || '')}</span>
            </div>
          `,
        )
        .join('')}
    </div>
  `;
}

function renderTaskDetails(data) {
  const submission = data.submission || {};
  const book = data.book;
  const article = data.article;
  const draft = data.draft;
  const draftContent = draft?.content || article?.content || '';

  return `
    <div class="task-details-container">
      <h3>${escapeHtml(submission.title || '-')}</h3>
      <p><strong>Autor:</strong> ${escapeHtml(submission.author_name || '-')}</p>
      <p>
        <strong>Status:</strong>
        <span id="task-status" class="task-status ${statusClass(submission.status)}">${escapeHtml(statusLabel(submission.status))}</span>
      </p>
      <p><strong>Criado em:</strong> ${formatDate(submission.created_at)}</p>
      <p><strong>Atualizado em:</strong> ${formatDate(submission.updated_at)}</p>
      <p><strong>Amazon:</strong> <a href="${escapeHtml(submission.amazon_url || '#')}" target="_blank" rel="noopener noreferrer">abrir link</a></p>

      <h4>Progresso</h4>
      ${renderProgress(data.progress?.steps || [])}

      <div class="task-actions" id="task-actions">
        <button id="action-generate-context" class="btn btn-secondary" type="button">Generate Context</button>
        <button id="action-generate-article" class="btn btn-secondary" type="button">Generate Article</button>
        <button id="action-retry" class="btn btn-secondary" type="button">Retry</button>
        <button id="action-publish" class="btn btn-primary" type="button">Publish to WordPress</button>
      </div>

      <div id="task-action-result" class="form-result" style="display:none"></div>

      ${article
        ? `
          <div class="article-editor-section">
            <h4>Draft / Edição de Artigo</h4>
            <label class="form-label" for="article-title-input">Título</label>
            <input id="article-title-input" class="form-input" value="${escapeHtml(article.title || '')}" />

            <label class="form-label" for="article-content-editor">Conteúdo (Markdown)</label>
            <textarea id="article-content-editor" class="form-textarea" rows="14">${escapeHtml(draftContent)}</textarea>

            <div class="task-actions">
              <button id="action-save-draft" class="btn btn-secondary" type="button">Salvar Draft</button>
              <button id="action-save-article" class="btn btn-primary" type="button">Salvar Artigo</button>
            </div>

            <h5>Preview</h5>
            <div id="article-preview" class="article-preview"></div>
          </div>
        `
        : '<p class="text-muted">Artigo ainda não foi gerado para esta tarefa.</p>'}

      ${book
        ? `
          <details class="details-block">
            <summary>Dados extraídos</summary>
            <pre>${escapeHtml(JSON.stringify(book.extracted || {}, null, 2))}</pre>
          </details>
        `
        : ''}

      ${data.knowledge_base
        ? `
          <details class="details-block">
            <summary>Knowledge Base</summary>
            <pre>${escapeHtml(String(data.knowledge_base.markdown_content || '').slice(0, 4000))}</pre>
          </details>
        `
        : ''}
    </div>
  `;
}

function showTaskActionResult(message, isError = false) {
  const resultEl = document.getElementById('task-action-result');
  if (!resultEl) return;

  resultEl.style.display = 'block';
  resultEl.className = `form-result ${isError ? 'error' : 'success'}`;
  resultEl.textContent = message;
}

async function executeTaskAction(url, method = 'POST', payload = null) {
  const response = await fetch(url, {
    method,
    headers: payload ? { 'Content-Type': 'application/json' } : undefined,
    body: payload ? JSON.stringify(payload) : undefined,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(parseApiError(data, 'Ação falhou'));
  return data;
}

function wireTaskActions(taskId, taskData) {
  const generateContextBtn = document.getElementById('action-generate-context');
  const generateArticleBtn = document.getElementById('action-generate-article');
  const retryBtn = document.getElementById('action-retry');
  const publishBtn = document.getElementById('action-publish');

  if (generateContextBtn) {
    generateContextBtn.addEventListener('click', async () => {
      try {
        await executeTaskAction(`/tasks/${taskId}/generate_context`);
        showTaskActionResult('Geração de contexto enfileirada com sucesso.');
        setTimeout(() => fetchTaskDetails(taskId), 1000);
      } catch (err) {
        showTaskActionResult(normalizeError(err, 'Falha ao enfileirar contexto'), true);
      }
    });
  }

  if (generateArticleBtn) {
    generateArticleBtn.addEventListener('click', async () => {
      try {
        await executeTaskAction(`/tasks/${taskId}/generate_article`);
        showTaskActionResult('Geração de artigo enfileirada com sucesso.');
        setTimeout(() => fetchTaskDetails(taskId), 1000);
      } catch (err) {
        showTaskActionResult(normalizeError(err, 'Falha ao enfileirar artigo'), true);
      }
    });
  }

  if (retryBtn) {
    retryBtn.addEventListener('click', async () => {
      try {
        await executeTaskAction(`/tasks/${taskId}/retry`);
        showTaskActionResult('Retry da tarefa enfileirado com sucesso.');
        setTimeout(() => fetchTaskDetails(taskId), 1000);
      } catch (err) {
        showTaskActionResult(normalizeError(err, 'Falha ao executar retry'), true);
      }
    });
  }

  if (publishBtn) {
    publishBtn.addEventListener('click', async () => {
      try {
        await executeTaskAction(`/tasks/${taskId}/publish_article`);
        showTaskActionResult('Publicação enfileirada com sucesso.');
        setTimeout(() => fetchTaskDetails(taskId), 1000);
      } catch (err) {
        showTaskActionResult(normalizeError(err, 'Falha ao enfileirar publicação'), true);
      }
    });
  }

  const contentEditor = document.getElementById('article-content-editor');
  const preview = document.getElementById('article-preview');
  const saveDraftBtn = document.getElementById('action-save-draft');
  const saveArticleBtn = document.getElementById('action-save-article');
  const titleInput = document.getElementById('article-title-input');

  function refreshPreview() {
    if (!preview || !contentEditor) return;
    preview.innerHTML = markdownToHtml(contentEditor.value);
  }

  if (contentEditor && preview) {
    contentEditor.addEventListener('input', refreshPreview);
    refreshPreview();
  }

  if (saveDraftBtn && contentEditor) {
    saveDraftBtn.addEventListener('click', async () => {
      const content = contentEditor.value.trim();
      if (!content) {
        showTaskActionResult('Conteúdo do draft é obrigatório.', true);
        return;
      }

      try {
        await executeTaskAction(`/tasks/${taskId}/draft_article`, 'POST', { content });
        showTaskActionResult('Draft salvo com sucesso.');
      } catch (err) {
        showTaskActionResult(normalizeError(err, 'Falha ao salvar draft'), true);
      }
    });
  }

  if (saveArticleBtn && contentEditor && titleInput && taskData?.article?.id) {
    saveArticleBtn.addEventListener('click', async () => {
      const content = contentEditor.value.trim();
      const title = titleInput.value.trim();
      if (!content || !title) {
        showTaskActionResult('Título e conteúdo do artigo são obrigatórios.', true);
        return;
      }

      try {
        await executeTaskAction(`/articles/${taskData.article.id}`, 'PATCH', {
          title,
          content,
        });
        showTaskActionResult('Artigo atualizado com sucesso.');
      } catch (err) {
        showTaskActionResult(normalizeError(err, 'Falha ao atualizar artigo'), true);
      }
    });
  }
}

async function fetchTaskDetails(taskId) {
  setModalContent('<div style="padding:20px">Carregando detalhes...</div>');

  try {
    const response = await fetch(`/tasks/${taskId}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(data, 'Falha ao carregar detalhes da tarefa'));

    setModalContent(renderTaskDetails(data));
    wireTaskActions(taskId, data);
  } catch (err) {
    setModalContent(`<div style="padding:20px" class="form-result error">Erro: ${escapeHtml(normalizeError(err, 'Falha ao carregar detalhes'))}</div>`);
  }
}

function updateScheduleState() {
  if (!runImmediatelyInput || !scheduleInput) return;
  const runNow = runImmediatelyInput.checked;
  scheduleInput.disabled = runNow;
  scheduleInput.required = !runNow;
  if (runNow) scheduleInput.value = '';
}

function createOtherLinkInput(value = '') {
  const wrapper = document.createElement('div');
  wrapper.className = 'other-link-row';
  wrapper.innerHTML = `
    <input type="url" class="form-input other-link" placeholder="https://..." value="${escapeHtml(value)}">
    <button type="button" class="btn btn-secondary remove-link-btn">Remover</button>
  `;

  const removeBtn = wrapper.querySelector('.remove-link-btn');
  if (removeBtn) {
    removeBtn.addEventListener('click', () => {
      const allRows = otherLinksContainer ? otherLinksContainer.querySelectorAll('.other-link-row') : [];
      if (allRows.length <= 1) {
        const input = wrapper.querySelector('.other-link');
        if (input) input.value = '';
        return;
      }
      wrapper.remove();
    });
  }

  return wrapper;
}

function resetSubmitFormLinks() {
  if (!otherLinksContainer) return;
  otherLinksContainer.innerHTML = '';
  otherLinksContainer.appendChild(createOtherLinkInput());
}

function collectSubmitPayload() {
  const title = document.getElementById('title')?.value.trim();
  const authorName = document.getElementById('author_name')?.value.trim();
  const amazonUrl = document.getElementById('amazon_url')?.value.trim();
  const goodreadsUrl = document.getElementById('goodreads_url')?.value.trim();
  const authorSite = document.getElementById('author_site')?.value.trim();
  const textualInformation = document.getElementById('textual_information')?.value.trim();
  const mainCategory = document.getElementById('main_category')?.value.trim();
  const articleStatus = document.getElementById('article_status')?.value;
  const runImmediately = !!runImmediatelyInput?.checked;
  const scheduleExecution = scheduleInput?.value;
  const userApprovalRequired = !!document.getElementById('user_approval_required')?.checked;

  if (!title || !authorName || !amazonUrl) {
    throw new Error('Preencha os campos obrigatórios: título, autor e link Amazon.');
  }

  if (!/^https?:\/\//i.test(amazonUrl)) {
    throw new Error('Amazon URL deve iniciar com http:// ou https://');
  }

  if (!runImmediately && !scheduleExecution) {
    throw new Error('Informe data/hora de agendamento quando Run immediately estiver desmarcado.');
  }

  const payload = {
    title,
    author_name: authorName,
    amazon_url: amazonUrl,
    run_immediately: runImmediately,
    user_approval_required: userApprovalRequired,
  };

  if (goodreadsUrl) payload.goodreads_url = goodreadsUrl;
  if (authorSite) payload.author_site = authorSite;
  if (textualInformation) payload.textual_information = textualInformation;
  if (mainCategory) payload.main_category = mainCategory;
  if (articleStatus) payload.article_status = articleStatus;
  if (!runImmediately) payload.schedule_execution = scheduleExecution;

  if (otherLinksContainer) {
    const links = Array.from(otherLinksContainer.querySelectorAll('.other-link'))
      .map((input) => input.value.trim())
      .filter((url) => url);

    const invalid = links.find((url) => !/^https?:\/\//i.test(url));
    if (invalid) {
      throw new Error(`Link adicional inválido: ${invalid}`);
    }

    if (links.length) payload.other_links = links;
  }

  return payload;
}

if (submitForm) {
  submitForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    submitResult.textContent = 'Enviando...';
    submitResult.className = 'form-result';

    try {
      const payload = collectSubmitPayload();
      const response = await fetch('/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseApiError(data, 'Falha no envio da task'));

      submitResult.className = 'form-result success';
      submitResult.textContent = `Task criada com sucesso: ${data.id}`;

      submitForm.reset();
      updateScheduleState();
      resetSubmitFormLinks();

      skip = 0;
      fetchTasks();
      fetchStats();
    } catch (err) {
      submitResult.className = 'form-result error';
      submitResult.textContent = normalizeError(err, 'Falha no envio da task');
    }
  });
}

function setCredentialFormMode(editing) {
  const submitButton = credForm?.querySelector('button[type="submit"]');
  if (!submitButton) return;
  submitButton.textContent = editing ? 'Atualizar credencial' : 'Salvar credencial';
}

function resetCredentialForm() {
  editingCredentialId = null;
  if (!credForm) return;

  credForm.reset();
  const encrypted = credForm.querySelector('input[name="encrypted"]');
  const active = credForm.querySelector('input[name="active"]');
  if (encrypted) encrypted.checked = true;
  if (active) active.checked = true;
  setCredentialFormMode(false);
}

function renderCredentialItem(credential) {
  const li = document.createElement('li');
  li.className = 'item-card';

  const active = !!credential.active;
  const status = active ? 'Ativa' : 'Inativa';
  const lastUsed = formatDate(credential.last_used_at);

  li.innerHTML = `
    <div>
      <strong>${escapeHtml(credential.name || credential.service || '-')}</strong>
      <div class="text-muted small">Service: ${escapeHtml(credential.service || '-')} | Key: ${escapeHtml(credential.key || '****')}</div>
      <div class="text-muted small">Criada: ${formatDate(credential.created_at)} | Último uso: ${lastUsed}</div>
      <span class="task-status ${active ? 'status-success' : 'status-warning'}">${status}</span>
    </div>
    <div class="item-actions">
      <button type="button" class="btn btn-secondary btn-xs" data-action="edit">Edit</button>
      <button type="button" class="btn btn-secondary btn-xs" data-action="toggle">${active ? 'Inativar' : 'Ativar'}</button>
      <button type="button" class="btn btn-secondary btn-xs" data-action="delete">Delete</button>
    </div>
  `;

  li.querySelector('[data-action="edit"]')?.addEventListener('click', () => {
    editingCredentialId = credential.id;

    const service = credForm?.querySelector('#cred-service');
    const name = credForm?.querySelector('#cred-name');
    const key = credForm?.querySelector('#cred-key');
    const username = credForm?.querySelector('#cred-username');
    const activeInput = credForm?.querySelector('input[name="active"]');

    if (service) service.value = credential.service || 'openai';
    if (name) name.value = credential.name || '';
    if (key) key.value = '';
    if (username) username.value = credential.username_email || '';
    if (activeInput) activeInput.checked = !!credential.active;

    setCredentialFormMode(true);
  });

  li.querySelector('[data-action="toggle"]')?.addEventListener('click', async () => {
    try {
      const response = await fetch(`/settings/credentials/${credential.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active: !active }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseApiError(data, 'Falha ao atualizar credencial'));

      fetchCredentials();
    } catch (err) {
      credResult.className = 'form-result error';
      credResult.textContent = normalizeError(err, 'Falha ao atualizar credencial');
    }
  });

  li.querySelector('[data-action="delete"]')?.addEventListener('click', async () => {
    if (!confirm('Excluir esta credencial?')) return;

    try {
      const response = await fetch(`/settings/credentials/${credential.id}`, { method: 'DELETE' });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(parseApiError(data, 'Falha ao excluir credencial'));
      }
      if (editingCredentialId === credential.id) resetCredentialForm();
      fetchCredentials();
    } catch (err) {
      credResult.className = 'form-result error';
      credResult.textContent = normalizeError(err, 'Falha ao excluir credencial');
    }
  });

  return li;
}

async function fetchCredentials() {
  if (!credList) return;

  credList.innerHTML = '<li class="loading">Carregando...</li>';

  try {
    const response = await fetch('/settings/credentials');
    const items = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(items, 'Falha ao carregar credenciais'));

    credList.innerHTML = '';
    if (!Array.isArray(items) || items.length === 0) {
      credList.innerHTML = '<li class="empty-state">Nenhuma credencial configurada</li>';
      return;
    }

    items.forEach((item) => credList.appendChild(renderCredentialItem(item)));
  } catch (err) {
    credList.innerHTML = `<li class="empty-state">Erro: ${escapeHtml(normalizeError(err, 'Falha ao carregar credenciais'))}</li>`;
  }
}

if (credForm) {
  credForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    credResult.className = 'form-result';
    credResult.textContent = editingCredentialId ? 'Atualizando...' : 'Salvando...';

    const service = credForm.querySelector('#cred-service')?.value;
    const name = credForm.querySelector('#cred-name')?.value.trim();
    const key = credForm.querySelector('#cred-key')?.value.trim();
    const usernameEmail = credForm.querySelector('#cred-username')?.value.trim();
    const encrypted = !!credForm.querySelector('input[name="encrypted"]')?.checked;
    const active = !!credForm.querySelector('input[name="active"]')?.checked;

    try {
      let response;
      if (editingCredentialId) {
        const payload = {
          name: name || undefined,
          username_email: usernameEmail || undefined,
          active,
        };
        if (key) payload.key = key;

        response = await fetch(`/settings/credentials/${editingCredentialId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
      } else {
        if (!service || !name || !key) {
          throw new Error('Service, Credential Name e API Key são obrigatórios.');
        }

        response = await fetch('/settings/credentials', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            service,
            name,
            key,
            username_email: usernameEmail || undefined,
            encrypted,
            active,
          }),
        });
      }

      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseApiError(data, 'Falha ao salvar credencial'));

      credResult.className = 'form-result success';
      credResult.textContent = editingCredentialId ? 'Credencial atualizada com sucesso.' : 'Credencial salva com sucesso.';

      resetCredentialForm();
      fetchCredentials();
    } catch (err) {
      credResult.className = 'form-result error';
      credResult.textContent = normalizeError(err, 'Falha ao salvar credencial');
    }
  });
}

function setPromptFormMode(editing) {
  const submitButton = promptForm?.querySelector('button[type="submit"]');
  if (!submitButton) return;
  submitButton.textContent = editing ? 'Atualizar prompt' : 'Salvar prompt';
}

function resetPromptForm() {
  editingPromptId = null;
  if (!promptForm) return;

  promptForm.reset();
  const active = promptForm.querySelector('input[name="active"]');
  if (active) active.checked = true;
  const model = promptForm.querySelector('#prompt-model');
  const temperature = promptForm.querySelector('#prompt-temp');
  const maxTokens = promptForm.querySelector('#prompt-tokens');
  if (model) model.value = 'gpt-4o-mini';
  if (temperature) temperature.value = '0.7';
  if (maxTokens) maxTokens.value = '800';

  setPromptFormMode(false);
}

function renderPromptItem(prompt) {
  const li = document.createElement('li');
  li.className = 'item-card';

  const active = !!prompt.active;
  const shortSystem = (prompt.system_prompt || '').slice(0, 160);

  li.innerHTML = `
    <div>
      <strong>${escapeHtml(prompt.name || '-')}</strong>
      <div class="text-muted small">${escapeHtml(prompt.short_description || prompt.purpose || '')}</div>
      <div class="text-muted small">Purpose: ${escapeHtml(prompt.purpose || '-')} | Model: ${escapeHtml(prompt.model_id || '-')}</div>
      <div class="text-muted small">${escapeHtml(shortSystem)}${(prompt.system_prompt || '').length > 160 ? '...' : ''}</div>
      <span class="task-status ${active ? 'status-success' : 'status-warning'}">${active ? 'Ativo' : 'Inativo'}</span>
    </div>
    <div class="item-actions">
      <button type="button" class="btn btn-secondary btn-xs" data-action="edit">Edit</button>
      <button type="button" class="btn btn-secondary btn-xs" data-action="toggle">${active ? 'Desativar' : 'Ativar'}</button>
      <button type="button" class="btn btn-secondary btn-xs" data-action="delete">Delete</button>
    </div>
  `;

  li.querySelector('[data-action="edit"]')?.addEventListener('click', () => {
    editingPromptId = prompt.id;

    promptForm.querySelector('#prompt-name').value = prompt.name || '';
    promptForm.querySelector('#prompt-purpose').value = prompt.purpose || '';
    promptForm.querySelector('#prompt-short').value = prompt.short_description || '';
    promptForm.querySelector('#prompt-system').value = prompt.system_prompt || '';
    promptForm.querySelector('#prompt-user').value = prompt.user_prompt || '';
    promptForm.querySelector('#prompt-model').value = prompt.model_id || 'gpt-4o-mini';
    promptForm.querySelector('#prompt-temp').value = String(prompt.temperature ?? 0.7);
    promptForm.querySelector('#prompt-tokens').value = String(prompt.max_tokens ?? 800);
    promptForm.querySelector('input[name="active"]').checked = !!prompt.active;

    setPromptFormMode(true);
  });

  li.querySelector('[data-action="toggle"]')?.addEventListener('click', async () => {
    try {
      const response = await fetch(`/settings/prompts/${prompt.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active: !active }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseApiError(data, 'Falha ao atualizar prompt'));

      fetchPrompts();
    } catch (err) {
      promptResult.className = 'form-result error';
      promptResult.textContent = normalizeError(err, 'Falha ao atualizar prompt');
    }
  });

  li.querySelector('[data-action="delete"]')?.addEventListener('click', async () => {
    if (!confirm('Excluir este prompt?')) return;

    try {
      const response = await fetch(`/settings/prompts/${prompt.id}`, { method: 'DELETE' });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(parseApiError(data, 'Falha ao excluir prompt'));
      }
      if (editingPromptId === prompt.id) resetPromptForm();
      fetchPrompts();
    } catch (err) {
      promptResult.className = 'form-result error';
      promptResult.textContent = normalizeError(err, 'Falha ao excluir prompt');
    }
  });

  return li;
}

async function fetchPrompts() {
  if (!promptList) return;

  promptList.innerHTML = '<li class="loading">Carregando...</li>';

  try {
    const response = await fetch('/settings/prompts');
    const items = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(items, 'Falha ao carregar prompts'));

    promptList.innerHTML = '';
    if (!Array.isArray(items) || items.length === 0) {
      promptList.innerHTML = '<li class="empty-state">Nenhum prompt configurado</li>';
      return;
    }

    items.forEach((item) => promptList.appendChild(renderPromptItem(item)));
  } catch (err) {
    promptList.innerHTML = `<li class="empty-state">Erro: ${escapeHtml(normalizeError(err, 'Falha ao carregar prompts'))}</li>`;
  }
}

if (promptForm) {
  promptForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    promptResult.className = 'form-result';
    promptResult.textContent = editingPromptId ? 'Atualizando...' : 'Salvando...';

    const payload = {
      name: promptForm.querySelector('#prompt-name')?.value.trim(),
      purpose: promptForm.querySelector('#prompt-purpose')?.value.trim(),
      short_description: promptForm.querySelector('#prompt-short')?.value.trim() || undefined,
      system_prompt: promptForm.querySelector('#prompt-system')?.value,
      user_prompt: promptForm.querySelector('#prompt-user')?.value,
      model_id: promptForm.querySelector('#prompt-model')?.value.trim() || 'gpt-4o-mini',
      temperature: parseFloat(promptForm.querySelector('#prompt-temp')?.value || '0.7'),
      max_tokens: parseInt(promptForm.querySelector('#prompt-tokens')?.value || '800', 10),
      active: !!promptForm.querySelector('input[name="active"]')?.checked,
    };

    try {
      if (!payload.name || !payload.purpose || !payload.system_prompt || !payload.user_prompt) {
        throw new Error('Prompt name, purpose, system prompt e user prompt são obrigatórios.');
      }

      const response = await fetch(editingPromptId ? `/settings/prompts/${editingPromptId}` : '/settings/prompts', {
        method: editingPromptId ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseApiError(data, 'Falha ao salvar prompt'));

      promptResult.className = 'form-result success';
      promptResult.textContent = editingPromptId ? 'Prompt atualizado com sucesso.' : 'Prompt salvo com sucesso.';

      resetPromptForm();
      fetchPrompts();
    } catch (err) {
      promptResult.className = 'form-result error';
      promptResult.textContent = normalizeError(err, 'Falha ao salvar prompt');
    }
  });
}

if (refreshBtn) {
  refreshBtn.addEventListener('click', () => {
    skip = 0;
    fetchTasks();
    fetchStats();
  });
}

if (prevBtn) {
  prevBtn.addEventListener('click', () => {
    skip = Math.max(0, skip - limit);
    fetchTasks();
  });
}

if (nextBtn) {
  nextBtn.addEventListener('click', () => {
    skip += limit;
    fetchTasks();
  });
}

if (statusFilter) {
  statusFilter.addEventListener('change', () => {
    skip = 0;
    fetchTasks();
  });
}

if (searchInput) {
  searchInput.addEventListener('input', () => {
    window.clearTimeout(searchDebounceTimer);
    searchDebounceTimer = window.setTimeout(() => {
      skip = 0;
      fetchTasks();
    }, 300);
  });
}

if (runImmediatelyInput) {
  runImmediatelyInput.addEventListener('change', updateScheduleState);
}

if (addOtherLinkBtn) {
  addOtherLinkBtn.addEventListener('click', () => {
    if (otherLinksContainer) otherLinksContainer.appendChild(createOtherLinkInput());
  });
}

async function updateHealth() {
  const healthLabel = document.getElementById('health-status');
  const healthDot = document.querySelector('.health-badge .dot');
  if (!healthLabel || !healthDot) return;

  try {
    const response = await fetch('/health');
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.status !== 'ok') throw new Error('down');

    healthLabel.textContent = 'API online';
    healthDot.classList.add('online');
  } catch (_) {
    healthLabel.textContent = 'API offline';
    healthDot.classList.remove('online');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  showSection('tasks-section');

  updateScheduleState();
  resetSubmitFormLinks();

  setCredentialFormMode(false);
  setPromptFormMode(false);

  updateHealth();
  fetchStats();
  fetchTasks();
  fetchCredentials();
  fetchPrompts();
});
