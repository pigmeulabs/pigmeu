const navLinks = document.querySelectorAll('.nav-link');
const sections = document.querySelectorAll('.section');

const modal = document.getElementById('task-modal');
const modalContent = modal ? modal.querySelector('.modal-content') : null;

const submitForm = document.getElementById('submit-form');
const submitResult = document.getElementById('submit-result');

const credForm = document.getElementById('cred-form');
const credResult = document.getElementById('cred-result');
const credFormResult = document.getElementById('cred-form-result');
const credList = document.getElementById('cred-list');
const createCredentialBtn = document.getElementById('create-credential-btn');
const credentialModal = document.getElementById('credential-modal');
const credentialModalTitle = document.getElementById('credential-modal-title');
const credentialCancelBtn = document.getElementById('credential-cancel-btn');

const promptForm = document.getElementById('prompt-form');
const promptResult = document.getElementById('prompt-result');
const promptFormResult = document.getElementById('prompt-form-result');
const promptList = document.getElementById('prompt-list');
const createPromptBtn = document.getElementById('create-prompt-btn');
const promptModal = document.getElementById('prompt-modal');
const promptModalTitle = document.getElementById('prompt-modal-title');
const promptCancelBtn = document.getElementById('prompt-cancel-btn');

const taskEditModal = document.getElementById('task-edit-modal');
const taskEditForm = document.getElementById('task-edit-form');
const taskEditResult = document.getElementById('task-edit-result');
const taskEditCancelBtn = document.getElementById('task-edit-cancel-btn');
const taskEditRunImmediatelyInput = document.getElementById('task-edit-run-immediately');
const taskEditScheduleInput = document.getElementById('task-edit-schedule-execution');

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
const otherLinksContainer = document.getElementById('other-links-container');

let skip = 0;
const limit = 10;
let currentTaskId = null;
let currentTaskDetails = null;
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

function toDatetimeLocalValue(value) {
  if (!value) return '';
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return '';
  const pad = (n) => String(n).padStart(2, '0');
  return `${dt.getFullYear()}-${pad(dt.getMonth() + 1)}-${pad(dt.getDate())}T${pad(dt.getHours())}:${pad(dt.getMinutes())}`;
}

function toIsoDateTime(localValue) {
  if (!localValue) return null;
  const dt = new Date(localValue);
  if (Number.isNaN(dt.getTime())) return null;
  return dt.toISOString();
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
    'analytics-section': 'Analytics',
    'tasks-section': 'Tasks Dashboard',
    'content-copilot-section': 'Content Copilot',
    'submit-section': 'Book Review',
    'articles-section': 'Articles',
    'social-media-section': 'Social media',
    'seo-tools-section': 'SEO Tools',
    'settings-section': 'Settings',
    'credentials-section': 'Credentials',
    'content-schemas-section': 'Content Schemas',
    'prompts-section': 'Prompts',
    'logout-section': 'Logout',
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
  currentTaskDetails = null;
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

function bindOverlayModalClose(modalEl, onClose) {
  if (!modalEl) return;
  modalEl.addEventListener('click', (event) => {
    const isClose = event.target.classList?.contains('modal-close');
    if (event.target === modalEl || isClose) onClose();
  });
}

function openOverlayModal(modalEl) {
  if (modalEl) modalEl.classList.add('active');
}

function closeOverlayModal(modalEl) {
  if (modalEl) modalEl.classList.remove('active');
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
      <div class="task-card-meta-actions">
        <span class="text-muted small">${formatDate(task.updated_at)}</span>
        <button type="button" class="btn btn-danger btn-xs task-card-delete-btn">Deletar</button>
      </div>
    </div>
  `;

  const deleteBtn = card.querySelector('.task-card-delete-btn');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async (event) => {
      event.stopPropagation();
      const confirmed = confirm(`Excluir tarefa "${task.title || task.id}"?`);
      if (!confirmed) return;

      try {
        deleteBtn.disabled = true;
        await deleteTaskById(task.id);
      } catch (err) {
        alert(normalizeError(err, 'Falha ao excluir tarefa'));
      } finally {
        deleteBtn.disabled = false;
      }
    });
  }

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

function getStepReprocessConfig(taskId, stage) {
  if (!taskId || !stage) return null;

  const makeStepRetryConfig = (targetStage, successMessage, errorMessage) => ({
    url: `/tasks/${taskId}/retry_step`,
    method: 'POST',
    payload: { stage: targetStage },
    successMessage,
    errorMessage,
  });

  const map = {
    amazon_scrape: makeStepRetryConfig(
      'amazon_scrape',
      'Reprocessamento de scraping Amazon enfileirado com sucesso.',
      'Falha ao reprocessar scraping Amazon'
    ),
    additional_links_scrape: makeStepRetryConfig(
      'additional_links_scrape',
      'Reprocessamento de links adicionais enfileirado com sucesso.',
      'Falha ao reprocessar links adicionais'
    ),
    summarize_additional_links: makeStepRetryConfig(
      'summarize_additional_links',
      'Reprocessamento de resumo de links enfileirado com sucesso.',
      'Falha ao reprocessar resumo de links'
    ),
    consolidate_book_data: makeStepRetryConfig(
      'consolidate_book_data',
      'Reprocessamento de consolidação enfileirado com sucesso.',
      'Falha ao reprocessar consolidação de dados'
    ),
    internet_research: makeStepRetryConfig(
      'internet_research',
      'Reprocessamento de pesquisa web enfileirado com sucesso.',
      'Falha ao reprocessar pesquisa web'
    ),
    context_generation: makeStepRetryConfig(
      'context_generation',
      'Reprocessamento de contexto enfileirado com sucesso.',
      'Falha ao reprocessar geração de contexto'
    ),
    article_generation: makeStepRetryConfig(
      'article_generation',
      'Reprocessamento de artigo enfileirado com sucesso.',
      'Falha ao reprocessar geração de artigo'
    ),
    pending_scrape: makeStepRetryConfig(
      'pending_scrape',
      'Reprocessamento de scraping enfileirado com sucesso.',
      'Falha ao reprocessar step de scraping'
    ),
    pending_context: makeStepRetryConfig(
      'pending_context',
      'Reprocessamento de contexto enfileirado com sucesso.',
      'Falha ao reprocessar step de contexto'
    ),
    pending_article: makeStepRetryConfig(
      'pending_article',
      'Reprocessamento de artigo enfileirado com sucesso.',
      'Falha ao reprocessar step de artigo'
    ),
    ready_for_review: makeStepRetryConfig(
      'ready_for_review',
      'Regeneração do artigo enfileirada com sucesso.',
      'Falha ao regenerar artigo'
    ),
  };

  return map[stage] || null;
}

function getStepContent(taskData, stage) {
  if (!taskData || !stage) return null;

  const submission = taskData.submission || {};
  const book = taskData.book;
  const summaries = Array.isArray(taskData.summaries) ? taskData.summaries : [];
  const kb = taskData.knowledge_base;
  const article = taskData.article;
  const draft = taskData.draft;
  const extracted = book?.extracted || {};

  if (stage === 'amazon_scrape' || stage === 'pending_scrape') {
    const extracted = book?.extracted;
    if (extracted && Object.keys(extracted).length > 0) {
      return {
        title: 'Conteúdo do step de scraping',
        type: 'json',
        value: JSON.stringify(extracted, null, 2),
      };
    }
    return null;
  }

  if (stage === 'additional_links_scrape') {
    const content = {
      configured_links: Array.isArray(submission.other_links) ? submission.other_links : [],
      additional_links_total: extracted.additional_links_total || 0,
      additional_links_processed: extracted.additional_links_processed || 0,
      link_bibliographic_candidates: extracted.link_bibliographic_candidates || [],
    };
    return {
      title: 'Conteúdo do step de links adicionais',
      type: 'json',
      value: JSON.stringify(content, null, 2),
    };
  }

  if (stage === 'summarize_additional_links') {
    if (!summaries.length) return null;
    return {
      title: 'Conteúdo do step de resumo de links',
      type: 'json',
      value: JSON.stringify(summaries, null, 2),
    };
  }

  if (stage === 'consolidate_book_data') {
    const consolidated = extracted.consolidated_bibliographic;
    if (!consolidated) return null;
    return {
      title: 'Conteúdo do step de consolidação',
      type: 'json',
      value: JSON.stringify(consolidated, null, 2),
    };
  }

  if (stage === 'internet_research') {
    const research = extracted.web_research;
    if (!research) return null;
    return {
      title: 'Conteúdo do step de pesquisa web',
      type: 'json',
      value: JSON.stringify(research, null, 2),
    };
  }

  if (stage === 'context_generation' || stage === 'pending_context') {
    const markdown = kb?.markdown_content;
    if (markdown) {
      return {
        title: 'Conteúdo do step de contexto',
        type: 'markdown',
        value: String(markdown),
      };
    }
    return null;
  }

  if (stage === 'article_generation' || stage === 'pending_article' || stage === 'ready_for_review') {
    const content = draft?.content || article?.content;
    if (content) {
      return {
        title: 'Conteúdo do step de artigo',
        type: 'markdown',
        value: String(content),
      };
    }
    return null;
  }

  return null;
}

const TASK_FLOW_DEFINITION = [
  { id: 'amazon_scrape', label: 'Amazon link scrap' },
  { id: 'additional_links_scrape', label: 'Additional links scrap' },
  { id: 'summarize_additional_links', label: 'Summarize additional links' },
  { id: 'consolidate_book_data', label: 'Consolidate book data' },
  { id: 'internet_research', label: 'Internet research' },
  { id: 'context_generation', label: 'Generate context' },
  { id: 'article_generation', label: 'Generate article' },
  { id: 'ready_for_review', label: 'Ready for review' },
];

function mapCurrentTaskStep(submission = {}) {
  const map = {
    amazon_scrape: 'amazon_scrape',
    scraping_amazon: 'amazon_scrape',
    pending_scrape: 'amazon_scrape',
    additional_links_processing: 'additional_links_scrape',
    additional_links_scrape: 'additional_links_scrape',
    summarize_additional_links: 'summarize_additional_links',
    bibliographic_consolidation: 'consolidate_book_data',
    consolidate_book_data: 'consolidate_book_data',
    internet_research: 'internet_research',
    context_generation: 'context_generation',
    pending_context: 'context_generation',
    context_generated: 'context_generation',
    article_generation: 'article_generation',
    pending_article: 'article_generation',
    article_generated: 'article_generation',
    ready_for_review: 'ready_for_review',
    approved: 'ready_for_review',
    published: 'ready_for_review',
  };

  const candidates = [submission.current_step, submission.status];
  for (const candidate of candidates) {
    const raw = String(candidate || '').toLowerCase();
    if (map[raw]) return map[raw];
  }
  return null;
}

function buildTaskFlowSteps(taskData) {
  const submission = taskData?.submission || {};
  const extracted = taskData?.book?.extracted || {};
  const status = String(submission.status || '').toLowerCase();

  const linksTotal = Array.isArray(submission.other_links) ? submission.other_links.length : 0;
  const linksProcessed = Number(extracted.additional_links_processed || 0);

  const hasAmazonData = !!taskData?.book?.id && Object.keys(extracted).length > 0;
  const hasLinksStep = linksTotal === 0 || linksProcessed > 0;
  const hasSummaryStep =
    linksTotal === 0 ||
    linksProcessed > 0 ||
    (Array.isArray(extracted.link_bibliographic_candidates) && extracted.link_bibliographic_candidates.length > 0);
  const hasConsolidated = !!extracted.consolidated_bibliographic;
  const hasResearch = !!(extracted.web_research && extracted.web_research.research_markdown);
  const hasContext = !!taskData?.knowledge_base?.markdown_content;
  const hasArticle = !!taskData?.article?.id;
  const isReady = ['ready_for_review', 'approved', 'published'].includes(status);

  const states = {};
  TASK_FLOW_DEFINITION.forEach((step) => {
    states[step.id] = 'to_do';
  });

  if (hasAmazonData) states.amazon_scrape = 'processed';
  if (hasLinksStep) states.additional_links_scrape = 'processed';
  if (hasSummaryStep) states.summarize_additional_links = 'processed';
  if (hasConsolidated) states.consolidate_book_data = 'processed';
  if (hasResearch) states.internet_research = 'processed';
  if (hasContext) states.context_generation = 'processed';
  if (hasArticle) states.article_generation = 'processed';
  if (isReady) states.ready_for_review = 'processed';

  const currentStep = mapCurrentTaskStep(submission);
  const currentIndex = TASK_FLOW_DEFINITION.findIndex((step) => step.id === currentStep);

  if (currentIndex >= 0) {
    for (let i = 0; i < currentIndex; i += 1) {
      const prevId = TASK_FLOW_DEFINITION[i].id;
      if (states[prevId] === 'to_do') states[prevId] = 'processed';
    }
  }

  const isFailed = ['scraping_failed', 'failed'].includes(status);
  if (isFailed && currentStep && states[currentStep] !== 'processed') {
    states[currentStep] = 'failed';
  } else if (currentStep && states[currentStep] === 'to_do') {
    states[currentStep] = 'current';
  }

  return TASK_FLOW_DEFINITION.map((step) => ({
    ...step,
    state: states[step.id] || 'to_do',
  }));
}

function getFlowStatusLabel(state) {
  if (state === 'processed') return 'processed';
  if (state === 'failed') return 'failed';
  if (state === 'current') return 'processing';
  return 'to do';
}

function renderTaskProgressTimeline(flowSteps = []) {
  if (!Array.isArray(flowSteps) || flowSteps.length === 0) return '<p class="text-muted">Sem progresso disponível</p>';

  return `
    <div class="task-progress-panel">
      <div class="task-flow-track">
      ${flowSteps
        .map((step) => {
          const isLast = step.id === flowSteps[flowSteps.length - 1].id;
          const nextStep = isLast ? null : flowSteps[flowSteps.findIndex((item) => item.id === step.id) + 1];
          const connectorState =
            !nextStep || step.state === 'to_do' || nextStep.state === 'to_do'
              ? 'neutral'
              : step.state === 'failed'
                ? 'failed'
                : 'processed';

          return `
            <div class="task-flow-step state-${step.state}">
              ${isLast ? '' : `<span class="task-flow-connector connector-${connectorState}"></span>`}
              <span class="task-flow-circle"></span>
              <span class="task-flow-label">${escapeHtml(step.label || step.id)}</span>
            </div>
          `;
        })
        .join('')}
      </div>
    </div>
  `;
}

function renderStepDetails(flowSteps = [], taskData = null) {
  if (!Array.isArray(flowSteps) || flowSteps.length === 0) return '<p class="text-muted">Sem steps disponíveis.</p>';

  return `
    <div class="steps-details-panel">
      ${flowSteps
        .map((step) => {
          const statusText = getFlowStatusLabel(step.state);
          const reprocessConfig = getStepReprocessConfig(currentTaskId, step.id);
          const canReprocess = !!reprocessConfig && step.state !== 'to_do';
          const hasContent = !!getStepContent(taskData, step.id);
          const canView = hasContent && step.state !== 'to_do';

          return `
            <div class="steps-row">
              <div class="steps-name">${escapeHtml(step.label)}</div>
              <div class="steps-actions">
                <span class="step-state-badge state-${step.state}">${escapeHtml(statusText)}</span>
                <button type="button" class="btn btn-secondary btn-xs step-action-reprocess" data-step-stage="${escapeHtml(step.id)}" ${canReprocess ? '' : 'disabled'}>
                  retry
                </button>
                <button type="button" class="btn btn-secondary btn-xs step-action-view" data-step-stage="${escapeHtml(step.id)}" ${canView ? '' : 'disabled'}>
                  view content
                </button>
              </div>
            </div>
          `;
        })
        .join('')}
    </div>
  `;
}

function renderTaskDetails(data) {
  const submission = data.submission || {};
  const flowSteps = buildTaskFlowSteps(data);

  return `
    <div class="task-details-container">
      <div class="task-details-top">
        <h3 class="task-details-title">Task details: Book Review</h3>
        <div class="task-details-top-actions">
          <button id="action-edit-task" class="btn btn-primary" type="button">Alterar tarefa</button>
          <button id="action-delete-task" class="btn btn-danger" type="button">Deletar</button>
        </div>
      </div>
      <div class="task-details-divider"></div>

      <div class="task-meta-grid">
        <div class="task-meta-col">
          <p class="task-meta-line"><strong>Books:</strong> ${escapeHtml(submission.title || '-')}</p>
          <p class="task-meta-line"><strong>Created:</strong> ${formatDate(submission.created_at)}</p>
        </div>
        <div class="task-meta-col">
          <p class="task-meta-line"><strong>Author:</strong> ${escapeHtml(submission.author_name || '-')}</p>
          <p class="task-meta-line"><strong>Last update:</strong> ${formatDate(submission.updated_at)}</p>
        </div>
      </div>

      <h4 class="task-section-title">Task Progress</h4>
      ${renderTaskProgressTimeline(flowSteps)}

      <h4 class="task-section-title">Steps details</h4>
      ${renderStepDetails(flowSteps, data)}
      <div id="task-action-result" class="form-result" style="display:none"></div>
      <div id="step-content-viewer" class="details-block" style="display:none"></div>
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

async function deleteTaskById(taskId, { closeDetails = false } = {}) {
  await executeTaskAction(`/tasks/${taskId}`, 'DELETE');

  if (closeDetails) {
    closeModal();
  }

  await Promise.all([fetchTasks(), fetchStats()]);
}

function wireTaskActions(taskId, taskData) {
  const editTaskBtn = document.getElementById('action-edit-task');
  const deleteTaskBtn = document.getElementById('action-delete-task');
  const stepContentViewer = document.getElementById('step-content-viewer');
  const reprocessButtons = document.querySelectorAll('.step-action-reprocess');
  const viewButtons = document.querySelectorAll('.step-action-view');

  if (editTaskBtn) {
    editTaskBtn.addEventListener('click', () => {
      openTaskEditModal(taskData?.submission || {});
    });
  }

  if (deleteTaskBtn) {
    deleteTaskBtn.addEventListener('click', async () => {
      const confirmed = confirm(`Excluir tarefa "${taskData?.submission?.title || taskId}"?`);
      if (!confirmed) return;

      try {
        deleteTaskBtn.disabled = true;
        await deleteTaskById(taskId, { closeDetails: true });
      } catch (err) {
        showTaskActionResult(normalizeError(err, 'Falha ao excluir tarefa'), true);
      } finally {
        deleteTaskBtn.disabled = false;
      }
    });
  }

  reprocessButtons.forEach((button) => {
    button.addEventListener('click', async () => {
      const stage = button.dataset.stepStage;
      const config = getStepReprocessConfig(taskId, stage);
      if (!config) {
        showTaskActionResult('Step sem ação de reprocessamento disponível.', true);
        return;
      }

      const stepLabel = button.closest('.steps-row')?.querySelector('.steps-name')?.textContent?.trim() || stage;
      const confirmed = confirm(
        `Ao reprocessar o passo "${stepLabel}", todos os demais passos já executados serão perdidos e executados novamente.\n\nDeseja continuar?`
      );
      if (!confirmed) return;

      try {
        button.disabled = true;
        await executeTaskAction(config.url, config.method || 'POST', config.payload || null);
        showTaskActionResult(config.successMessage);
        setTimeout(() => fetchTaskDetails(taskId), 1000);
      } catch (err) {
        showTaskActionResult(normalizeError(err, config.errorMessage), true);
      } finally {
        button.disabled = false;
      }
    });
  });

  viewButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const stage = button.dataset.stepStage;
      const content = getStepContent(taskData, stage);

      if (!stepContentViewer) return;
      stepContentViewer.style.display = 'block';

      if (!content) {
        stepContentViewer.innerHTML = `
          <h5>Conteúdo do step</h5>
          <p class="text-muted">Conteúdo ainda não disponível para este step.</p>
        `;
        return;
      }

      const body =
        content.type === 'json'
          ? `<pre>${escapeHtml(content.value)}</pre>`
          : `<div class="article-preview">${markdownToHtml(content.value)}</div>`;

      stepContentViewer.innerHTML = `
        <h5>${escapeHtml(content.title)}</h5>
        ${body}
      `;
    });
  });

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

    currentTaskDetails = data;
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

function updateTaskEditScheduleState() {
  if (!taskEditRunImmediatelyInput || !taskEditScheduleInput) return;
  const runNow = taskEditRunImmediatelyInput.checked;
  taskEditScheduleInput.disabled = runNow;
  taskEditScheduleInput.required = !runNow;
  if (runNow) taskEditScheduleInput.value = '';
}

function openTaskEditModal(submission) {
  if (!taskEditForm || !submission) return;

  taskEditForm.querySelector('#task-edit-title').value = submission.title || '';
  taskEditForm.querySelector('#task-edit-author-name').value = submission.author_name || '';
  taskEditForm.querySelector('#task-edit-amazon-url').value = submission.amazon_url || '';
  taskEditForm.querySelector('#task-edit-goodreads-url').value = submission.goodreads_url || '';
  taskEditForm.querySelector('#task-edit-author-site').value = submission.author_site || '';
  taskEditForm.querySelector('#task-edit-other-links').value = Array.isArray(submission.other_links) ? submission.other_links.join('\n') : '';
  taskEditForm.querySelector('#task-edit-textual-information').value = submission.textual_information || '';
  taskEditForm.querySelector('#task-edit-main-category').value = submission.main_category || '';
  taskEditForm.querySelector('#task-edit-article-status').value = submission.article_status || '';
  taskEditForm.querySelector('#task-edit-run-immediately').checked = submission.run_immediately !== false;
  taskEditForm.querySelector('#task-edit-schedule-execution').value = toDatetimeLocalValue(submission.schedule_execution);
  taskEditForm.querySelector('#task-edit-user-approval-required').checked = !!submission.user_approval_required;

  if (taskEditResult) {
    taskEditResult.className = 'form-result';
    taskEditResult.textContent = '';
  }

  updateTaskEditScheduleState();
  openOverlayModal(taskEditModal);
}

function closeTaskEditModal() {
  closeOverlayModal(taskEditModal);
}

function collectTaskEditPayload() {
  if (!taskEditForm) throw new Error('Formulário de edição indisponível.');

  const title = taskEditForm.querySelector('#task-edit-title')?.value.trim();
  const authorName = taskEditForm.querySelector('#task-edit-author-name')?.value.trim();
  const amazonUrl = taskEditForm.querySelector('#task-edit-amazon-url')?.value.trim();
  const goodreadsUrl = taskEditForm.querySelector('#task-edit-goodreads-url')?.value.trim();
  const authorSite = taskEditForm.querySelector('#task-edit-author-site')?.value.trim();
  const otherLinksRaw = taskEditForm.querySelector('#task-edit-other-links')?.value || '';
  const textualInformation = taskEditForm.querySelector('#task-edit-textual-information')?.value.trim();
  const mainCategory = taskEditForm.querySelector('#task-edit-main-category')?.value.trim();
  const articleStatus = taskEditForm.querySelector('#task-edit-article-status')?.value;
  const runImmediately = !!taskEditForm.querySelector('#task-edit-run-immediately')?.checked;
  const scheduleExecution = taskEditForm.querySelector('#task-edit-schedule-execution')?.value;
  const userApprovalRequired = !!taskEditForm.querySelector('#task-edit-user-approval-required')?.checked;

  if (!title || !authorName || !amazonUrl) {
    throw new Error('Preencha os campos obrigatórios: título, autor e link Amazon.');
  }

  if (!/^https?:\/\//i.test(amazonUrl)) {
    throw new Error('Amazon URL deve iniciar com http:// ou https://');
  }

  if (goodreadsUrl && !/^https?:\/\//i.test(goodreadsUrl)) {
    throw new Error('Goodreads URL deve iniciar com http:// ou https://');
  }

  if (authorSite && !/^https?:\/\//i.test(authorSite)) {
    throw new Error('Author site deve iniciar com http:// ou https://');
  }

  if (!runImmediately && !scheduleExecution) {
    throw new Error('Informe data/hora de agendamento quando Run immediately estiver desmarcado.');
  }

  const otherLinks = otherLinksRaw
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line);

  const invalid = otherLinks.find((url) => !/^https?:\/\//i.test(url));
  if (invalid) {
    throw new Error(`Link adicional inválido: ${invalid}`);
  }

  return {
    title,
    author_name: authorName,
    amazon_url: amazonUrl,
    goodreads_url: goodreadsUrl || null,
    author_site: authorSite || null,
    other_links: otherLinks,
    textual_information: textualInformation || null,
    run_immediately: runImmediately,
    schedule_execution: runImmediately ? null : toIsoDateTime(scheduleExecution),
    main_category: mainCategory || null,
    article_status: articleStatus || null,
    user_approval_required: userApprovalRequired,
  };
}

function updateOtherLinksUiState() {
  if (!otherLinksContainer) return;
  const rows = Array.from(otherLinksContainer.querySelectorAll('.other-link-row'));
  rows.forEach((row) => {
    const removeBtn = row.querySelector('.remove-link-btn');
    if (!removeBtn) return;
    removeBtn.style.visibility = rows.length <= 1 ? 'hidden' : 'visible';
  });
}

function createOtherLinkInput(value = '') {
  const wrapper = document.createElement('div');
  wrapper.className = 'other-link-row';
  wrapper.innerHTML = `
    <input type="url" class="form-input other-link" placeholder="Link to complementary content about book or author" value="${escapeHtml(value)}">
    <div class="other-link-actions">
      <button type="button" class="btn btn-secondary add-link-btn" aria-label="Adicionar link">+</button>
      <button type="button" class="btn btn-secondary remove-link-btn" aria-label="Remover link">-</button>
    </div>
  `;

  return wrapper;
}

function resetSubmitFormLinks() {
  if (!otherLinksContainer) return;
  otherLinksContainer.innerHTML = '';
  otherLinksContainer.appendChild(createOtherLinkInput());
  updateOtherLinksUiState();
}

function collectSubmitPayload() {
  const title = document.getElementById('title')?.value.trim();
  const authorName = document.getElementById('author_name')?.value.trim();
  const amazonUrl = document.getElementById('amazon_url')?.value.trim();
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

if (taskEditForm) {
  taskEditForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (!currentTaskId) {
      if (taskEditResult) {
        taskEditResult.className = 'form-result error';
        taskEditResult.textContent = 'Nenhuma tarefa selecionada para edição.';
      }
      return;
    }

    if (taskEditResult) {
      taskEditResult.className = 'form-result';
      taskEditResult.textContent = 'Salvando alterações...';
    }

    try {
      const submissionPayload = collectTaskEditPayload();
      await executeTaskAction(`/tasks/${currentTaskId}`, 'PATCH', { submission: submissionPayload });

      if (taskEditResult) {
        taskEditResult.className = 'form-result success';
        taskEditResult.textContent = 'Tarefa atualizada com sucesso.';
      }

      closeTaskEditModal();
      showTaskActionResult('Tarefa atualizada com sucesso.');
      fetchTaskDetails(currentTaskId);
      fetchTasks();
      fetchStats();
    } catch (err) {
      if (taskEditResult) {
        taskEditResult.className = 'form-result error';
        taskEditResult.textContent = normalizeError(err, 'Falha ao atualizar tarefa');
      }
    }
  });
}

if (taskEditRunImmediatelyInput) {
  taskEditRunImmediatelyInput.addEventListener('change', updateTaskEditScheduleState);
}

function setCredentialFormMode(editing) {
  const submitButton = credForm?.querySelector('button[type="submit"]');
  if (credentialModalTitle) credentialModalTitle.textContent = editing ? 'Edit Credential' : 'Create Credential';
  if (submitButton) submitButton.textContent = editing ? 'Save Changes' : 'Save';
}

function resetCredentialForm() {
  editingCredentialId = null;
  if (!credForm) return;

  credForm.reset();
  const encrypted = credForm.querySelector('input[name="encrypted"]');
  const active = credForm.querySelector('input[name="active"]');
  if (encrypted) encrypted.checked = true;
  if (active) active.checked = true;
  if (credFormResult) {
    credFormResult.className = 'form-result';
    credFormResult.textContent = '';
  }
  setCredentialFormMode(false);
}

function openCredentialModal(credential = null) {
  resetCredentialForm();
  if (credential && credForm) {
    editingCredentialId = credential.id;

    const service = credForm.querySelector('#cred-service');
    const name = credForm.querySelector('#cred-name');
    const key = credForm.querySelector('#cred-key');
    const username = credForm.querySelector('#cred-username');
    const activeInput = credForm.querySelector('input[name="active"]');

    if (service) service.value = credential.service || 'openai';
    if (name) name.value = credential.name || '';
    if (key) key.value = '';
    if (username) username.value = credential.username_email || '';
    if (activeInput) activeInput.checked = !!credential.active;

    setCredentialFormMode(true);
  }
  openOverlayModal(credentialModal);
}

function closeCredentialModal() {
  closeOverlayModal(credentialModal);
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
    openCredentialModal(credential);
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

      if (credResult) {
        credResult.className = 'form-result success';
        credResult.textContent = 'Credencial atualizada com sucesso.';
      }
      fetchCredentials();
    } catch (err) {
      if (credResult) {
        credResult.className = 'form-result error';
        credResult.textContent = normalizeError(err, 'Falha ao atualizar credencial');
      }
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
      if (credResult) {
        credResult.className = 'form-result success';
        credResult.textContent = 'Credencial excluída com sucesso.';
      }
      fetchCredentials();
    } catch (err) {
      if (credResult) {
        credResult.className = 'form-result error';
        credResult.textContent = normalizeError(err, 'Falha ao excluir credencial');
      }
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

    if (credFormResult) {
      credFormResult.className = 'form-result';
      credFormResult.textContent = editingCredentialId ? 'Atualizando...' : 'Salvando...';
    }

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

      if (credResult) {
        credResult.className = 'form-result success';
        credResult.textContent = editingCredentialId ? 'Credencial atualizada com sucesso.' : 'Credencial salva com sucesso.';
      }
      resetCredentialForm();
      closeCredentialModal();
      fetchCredentials();
    } catch (err) {
      if (credFormResult) {
        credFormResult.className = 'form-result error';
        credFormResult.textContent = normalizeError(err, 'Falha ao salvar credencial');
      }
    }
  });
}

function setPromptFormMode(editing) {
  const submitButton = promptForm?.querySelector('button[type="submit"]');
  if (promptModalTitle) promptModalTitle.textContent = editing ? 'Edit Prompt' : 'Create Prompt';
  if (submitButton) submitButton.textContent = editing ? 'Save Changes' : 'Save';
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
  if (promptFormResult) {
    promptFormResult.className = 'form-result';
    promptFormResult.textContent = '';
  }

  setPromptFormMode(false);
}

function openPromptModal(prompt = null) {
  resetPromptForm();
  if (prompt && promptForm) {
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
  }
  openOverlayModal(promptModal);
}

function closePromptModal() {
  closeOverlayModal(promptModal);
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
    openPromptModal(prompt);
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

      if (promptResult) {
        promptResult.className = 'form-result success';
        promptResult.textContent = 'Prompt atualizado com sucesso.';
      }
      fetchPrompts();
    } catch (err) {
      if (promptResult) {
        promptResult.className = 'form-result error';
        promptResult.textContent = normalizeError(err, 'Falha ao atualizar prompt');
      }
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
      if (promptResult) {
        promptResult.className = 'form-result success';
        promptResult.textContent = 'Prompt excluído com sucesso.';
      }
      fetchPrompts();
    } catch (err) {
      if (promptResult) {
        promptResult.className = 'form-result error';
        promptResult.textContent = normalizeError(err, 'Falha ao excluir prompt');
      }
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

    if (promptFormResult) {
      promptFormResult.className = 'form-result';
      promptFormResult.textContent = editingPromptId ? 'Atualizando...' : 'Salvando...';
    }

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

      if (promptResult) {
        promptResult.className = 'form-result success';
        promptResult.textContent = editingPromptId ? 'Prompt atualizado com sucesso.' : 'Prompt salvo com sucesso.';
      }
      resetPromptForm();
      closePromptModal();
      fetchPrompts();
    } catch (err) {
      if (promptFormResult) {
        promptFormResult.className = 'form-result error';
        promptFormResult.textContent = normalizeError(err, 'Falha ao salvar prompt');
      }
    }
  });
}

bindOverlayModalClose(credentialModal, closeCredentialModal);
bindOverlayModalClose(promptModal, closePromptModal);
bindOverlayModalClose(taskEditModal, closeTaskEditModal);

if (createCredentialBtn) {
  createCredentialBtn.addEventListener('click', () => openCredentialModal());
}

if (credentialCancelBtn) {
  credentialCancelBtn.addEventListener('click', closeCredentialModal);
}

if (createPromptBtn) {
  createPromptBtn.addEventListener('click', () => openPromptModal());
}

if (promptCancelBtn) {
  promptCancelBtn.addEventListener('click', closePromptModal);
}

if (taskEditCancelBtn) {
  taskEditCancelBtn.addEventListener('click', closeTaskEditModal);
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

if (otherLinksContainer) {
  otherLinksContainer.addEventListener('click', (event) => {
    const target = event.target instanceof Element ? event.target : null;
    if (!target) return;

    const addBtn = target.closest('.add-link-btn');
    if (addBtn) {
      otherLinksContainer.appendChild(createOtherLinkInput());
      updateOtherLinksUiState();
      const lastInput = otherLinksContainer.querySelector('.other-link-row:last-child .other-link');
      if (lastInput instanceof HTMLInputElement) lastInput.focus();
      return;
    }

    const removeBtn = target.closest('.remove-link-btn');
    if (removeBtn) {
      const row = removeBtn.closest('.other-link-row');
      if (!row) return;

      const allRows = otherLinksContainer.querySelectorAll('.other-link-row');
      if (allRows.length <= 1) {
        const input = row.querySelector('.other-link');
        if (input instanceof HTMLInputElement) input.value = '';
        return;
      }

      row.remove();
      updateOtherLinksUiState();
    }
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
  updateTaskEditScheduleState();
  resetSubmitFormLinks();

  setCredentialFormMode(false);
  setPromptFormMode(false);

  updateHealth();
  fetchStats();
  fetchTasks();
  fetchCredentials();
  fetchPrompts();
});
