const navLinks = document.querySelectorAll('.nav-link');
const sections = document.querySelectorAll('.section');

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
const taskDetailsContent = document.getElementById('task-details-content');
const backToTasksBtn = document.getElementById('back-to-tasks-btn');

const pipelinesGrid = document.getElementById('pipelines-grid');
const pipelinesResult = document.getElementById('pipelines-result');
const pipelineDetailsTitle = document.getElementById('pipeline-details-title');
const pipelineDetailsContent = document.getElementById('pipeline-details-content');
const layoutEl = document.querySelector('.layout');
const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');

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
let currentPipelineId = null;
let currentPipelineDetails = null;
const SIDEBAR_STORAGE_KEY = 'pigmeu.sidebar.collapsed';

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
    pending_scrape: 'Pending Scrape',
    scraping_amazon: 'Scraping Amazon',
    scraping_goodreads: 'Scraping Goodreads',
    context_generation: 'Generating Context',
    context_generated: 'Context Generated',
    pending_context: 'Pending Context',
    pending_article: 'Pending Article',
    article_generated: 'Article Generated',
    ready_for_review: 'Ready for Review',
    approved: 'Approved',
    published: 'Published',
    scraping_failed: 'Scrape Failed',
    failed: 'Failed',
  };
  return map[status] || status || '-';
}

function showSection(sectionId) {
  sections.forEach((section) => section.classList.remove('active'));
  document.getElementById(sectionId)?.classList.add('active');

  navLinks.forEach((link) => {
    link.classList.remove('active');
    if (link.dataset.section === sectionId) {
      link.classList.add('active');
      return;
    }
    if (sectionId === 'task-details-section' && link.dataset.section === 'tasks-section') {
      link.classList.add('active');
    }
  });

  const titleMap = {
    'analytics-section': 'Analytics',
    'tasks-section': 'Tasks Dashboard',
    'task-details-section': 'Task Details',
    'content-copilot-section': 'Content Copilot',
    'submit-section': 'Book Review',
    'articles-section': 'Articles',
    'social-media-section': 'Social Media',
    'seo-tools-section': 'SEO Tools',
    'settings-section': 'Settings',
    'credentials-section': 'Credentials',
    'content-schemas-section': 'Content Schemas',
    'prompts-section': 'Prompts',
    'pipelines-section': 'Pipelines',
    'logout-section': 'Logout',
  };
  const title = document.querySelector('.header-left h1');
  if (title) title.textContent = titleMap[sectionId] || 'Dashboard';

  if (sectionId === 'pipelines-section') {
    fetchPipelines();
  }
}

function applySidebarCollapsedState(collapsed) {
  if (!layoutEl) return;
  layoutEl.classList.toggle('sidebar-collapsed', !!collapsed);

  if (sidebarToggleBtn) {
    sidebarToggleBtn.classList.toggle('is-collapsed', !!collapsed);
    sidebarToggleBtn.setAttribute('aria-pressed', collapsed ? 'true' : 'false');
    const actionLabel = collapsed ? 'Expand Sidebar' : 'Collapse Sidebar';
    sidebarToggleBtn.setAttribute('aria-label', actionLabel);
    sidebarToggleBtn.setAttribute('title', collapsed ? 'Expand Sidebar' : 'Collapse Sidebar');
  }
}

function readSidebarCollapsedState() {
  try {
    return localStorage.getItem(SIDEBAR_STORAGE_KEY) === '1';
  } catch (_) {
    return false;
  }
}

function persistSidebarCollapsedState(collapsed) {
  try {
    localStorage.setItem(SIDEBAR_STORAGE_KEY, collapsed ? '1' : '0');
  } catch (_) {
    // no-op
  }
}

navLinks.forEach((link) => {
  link.addEventListener('click', (event) => {
    event.preventDefault();
    showSection(link.dataset.section);
  });
});

function setTaskDetailsContent(innerHtml) {
  if (!taskDetailsContent) return;
  taskDetailsContent.innerHTML = innerHtml;
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

  statsStrip.innerHTML = '<div class="loading">Loading metrics...</div>';
  try {
    const response = await fetch('/stats');
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(data, 'Failed to load metrics'));

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
        <span class="stat-label">Published</span>
        <span class="stat-value">${published}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Ready for Review</span>
        <span class="stat-value">${review}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Failed</span>
        <span class="stat-value">${failed}</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">Success Rate</span>
        <span class="stat-value">${(successRate * 100).toFixed(1)}%</span>
      </div>
    `;
  } catch (err) {
    statsStrip.innerHTML = `<div class="loading">Error: ${escapeHtml(normalizeError(err, 'Failed to load metrics'))}</div>`;
  }
}

function renderTaskCard(task) {
  const card = document.createElement('div');
  card.className = 'task-card clickable-card';

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
        <button type="button" class="btn btn-danger btn-xs task-card-delete-btn">Delete</button>
      </div>
    </div>
  `;

  const deleteBtn = card.querySelector('.task-card-delete-btn');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', async (event) => {
      event.stopPropagation();
      const confirmed = confirm(`Delete task "${task.title || task.id}"?`);
      if (!confirmed) return;

      try {
        deleteBtn.disabled = true;
        await deleteTaskById(task.id);
      } catch (err) {
        alert(normalizeError(err, 'Failed to delete task'));
      } finally {
        deleteBtn.disabled = false;
      }
    });
  }

  card.addEventListener('click', () => {
    currentTaskId = task.id;
    showSection('task-details-section');
    fetchTaskDetails(task.id);
  });

  return card;
}

async function fetchTasks() {
  if (!tasksGrid) return;

  tasksGrid.innerHTML = '<div class="loading">Loading tasks...</div>';

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
    if (!response.ok) throw new Error(parseApiError(data, 'Failed to load tasks'));

    tasksGrid.innerHTML = '';
    if (!Array.isArray(data.tasks) || data.tasks.length === 0) {
      tasksGrid.innerHTML = '<div class="loading">No tasks found</div>';
    } else {
      data.tasks.forEach((task) => tasksGrid.appendChild(renderTaskCard(task)));
    }

    const total = Number(data.total || 0);
    const count = Number(data.count || 0);
    const start = total > 0 ? Number(data.skip || 0) + 1 : 0;
    const end = total > 0 ? Number(data.skip || 0) + count : 0;

    if (paginationInfo) paginationInfo.textContent = `Showing ${start}-${end} of ${total}`;
    if (prevBtn) prevBtn.disabled = Number(data.skip || 0) <= 0;
    if (nextBtn) nextBtn.disabled = Number(data.skip || 0) + count >= total;
  } catch (err) {
    tasksGrid.innerHTML = `<div class="loading">Error: ${escapeHtml(normalizeError(err, 'Failed to load tasks'))}</div>`;
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
      'Amazon scraping retry queued successfully.',
      'Failed to retry Amazon scraping'
    ),
    additional_links_scrape: makeStepRetryConfig(
      'additional_links_scrape',
      'Additional links scraping retry queued successfully.',
      'Failed to retry additional links scraping'
    ),
    summarize_additional_links: makeStepRetryConfig(
      'summarize_additional_links',
      'Links summary retry queued successfully.',
      'Failed to retry links summary'
    ),
    consolidate_book_data: makeStepRetryConfig(
      'consolidate_book_data',
      'Consolidation retry queued successfully.',
      'Failed to retry data consolidation'
    ),
    internet_research: makeStepRetryConfig(
      'internet_research',
      'Web research retry queued successfully.',
      'Failed to retry web research'
    ),
    context_generation: makeStepRetryConfig(
      'context_generation',
      'Context generation retry queued successfully.',
      'Failed to retry context generation'
    ),
    article_generation: makeStepRetryConfig(
      'article_generation',
      'Article generation retry queued successfully.',
      'Failed to retry article generation'
    ),
    pending_scrape: makeStepRetryConfig(
      'pending_scrape',
      'Scraping retry queued successfully.',
      'Failed to retry scraping step'
    ),
    pending_context: makeStepRetryConfig(
      'pending_context',
      'Context generation retry queued successfully.',
      'Failed to retry context step'
    ),
    pending_article: makeStepRetryConfig(
      'pending_article',
      'Article generation retry queued successfully.',
      'Failed to retry article step'
    ),
    ready_for_review: makeStepRetryConfig(
      'ready_for_review',
      'Article regeneration queued successfully.',
      'Failed to regenerate article'
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
        title: 'Scraping Step Content',
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
      title: 'Additional Links Step Content',
      type: 'json',
      value: JSON.stringify(content, null, 2),
    };
  }

  if (stage === 'summarize_additional_links') {
    if (!summaries.length) return null;
    return {
      title: 'Links Summary Step Content',
      type: 'json',
      value: JSON.stringify(summaries, null, 2),
    };
  }

  if (stage === 'consolidate_book_data') {
    const consolidated = extracted.consolidated_bibliographic;
    if (!consolidated) return null;
    return {
      title: 'Consolidation Step Content',
      type: 'json',
      value: JSON.stringify(consolidated, null, 2),
    };
  }

  if (stage === 'internet_research') {
    const research = extracted.web_research;
    if (!research) return null;
    return {
      title: 'Web Research Step Content',
      type: 'json',
      value: JSON.stringify(research, null, 2),
    };
  }

  if (stage === 'context_generation' || stage === 'pending_context') {
    const markdown = kb?.markdown_content;
    if (markdown) {
      return {
        title: 'Context Step Content',
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
        title: 'Article Step Content',
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
    pending_context: 'additional_links_scrape',
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
  if (isFailed && currentStep) {
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
  if (!Array.isArray(flowSteps) || flowSteps.length === 0) return '<p class="text-muted">No progress available</p>';

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
  if (!Array.isArray(flowSteps) || flowSteps.length === 0) return '<p class="text-muted">No steps available.</p>';

  return `
    <div class="steps-details-panel">
      ${flowSteps
        .map((step) => {
          const statusText = getFlowStatusLabel(step.state);
          const reprocessConfig = getStepReprocessConfig(currentTaskId, step.id);
          const actionableState = step.state === 'processed' || step.state === 'failed';
          const canReprocess = !!reprocessConfig && actionableState;
          const canView = actionableState;

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
        <h3 class="task-details-title">Task Details: Book Review</h3>
        <div class="task-details-top-actions">
          <button id="action-edit-task" class="btn btn-primary" type="button">Edit Task</button>
          <button id="action-delete-task" class="btn btn-danger" type="button">Delete</button>
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

      <h4 class="task-section-title">Step Details</h4>
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
  if (!response.ok) throw new Error(parseApiError(data, 'Action failed'));
  return data;
}

async function deleteTaskById(taskId, { closeDetails = false } = {}) {
  await executeTaskAction(`/tasks/${taskId}`, 'DELETE');

  if (closeDetails) {
    showSection('tasks-section');
    currentTaskId = null;
    currentTaskDetails = null;
    setTaskDetailsContent('<p class="text-muted">Select a task to view details.</p>');
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
      const confirmed = confirm(`Delete task "${taskData?.submission?.title || taskId}"?`);
      if (!confirmed) return;

      try {
        deleteTaskBtn.disabled = true;
        await deleteTaskById(taskId, { closeDetails: true });
      } catch (err) {
        showTaskActionResult(normalizeError(err, 'Failed to delete task'), true);
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
        showTaskActionResult('No retry action available for this step.', true);
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
          <h5>Step Content</h5>
          <p class="text-muted">Content is not available for this step yet.</p>
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
        showTaskActionResult('Draft content is required.', true);
        return;
      }

      try {
        await executeTaskAction(`/tasks/${taskId}/draft_article`, 'POST', { content });
        showTaskActionResult('Draft saved successfully.');
      } catch (err) {
        showTaskActionResult(normalizeError(err, 'Failed to save draft'), true);
      }
    });
  }

  if (saveArticleBtn && contentEditor && titleInput && taskData?.article?.id) {
    saveArticleBtn.addEventListener('click', async () => {
      const content = contentEditor.value.trim();
      const title = titleInput.value.trim();
      if (!content || !title) {
        showTaskActionResult('Article title and content are required.', true);
        return;
      }

      try {
        await executeTaskAction(`/articles/${taskData.article.id}`, 'PATCH', {
          title,
          content,
        });
        showTaskActionResult('Article updated successfully.');
      } catch (err) {
        showTaskActionResult(normalizeError(err, 'Failed to update article'), true);
      }
    });
  }
}

async function fetchTaskDetails(taskId) {
  setTaskDetailsContent('<div class="loading">Loading details...</div>');

  try {
    const response = await fetch(`/tasks/${taskId}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(data, 'Failed to load task details'));

    currentTaskDetails = data;
    setTaskDetailsContent(renderTaskDetails(data));
    wireTaskActions(taskId, data);
  } catch (err) {
    setTaskDetailsContent(`<div class="form-result error">Error: ${escapeHtml(normalizeError(err, 'Failed to load details'))}</div>`);
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
  if (!taskEditForm) throw new Error('Edit form is unavailable.');

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
    throw new Error('Fill required fields: title, author, and Amazon link.');
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
    throw new Error('Informe data/hora of agendamento quando Run immediately estiver desmarcado.');
  }

  const otherLinks = otherLinksRaw
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line);

  const invalid = otherLinks.find((url) => !/^https?:\/\//i.test(url));
  if (invalid) {
    throw new Error(`Invalid additional link: ${invalid}`);
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
    throw new Error('Fill required fields: title, author, and Amazon link.');
  }

  if (!/^https?:\/\//i.test(amazonUrl)) {
    throw new Error('Amazon URL deve iniciar com http:// ou https://');
  }

  if (!runImmediately && !scheduleExecution) {
    throw new Error('Informe data/hora of agendamento quando Run immediately estiver desmarcado.');
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
      throw new Error(`Invalid additional link: ${invalid}`);
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
      if (!response.ok) throw new Error(parseApiError(data, 'Failed to submit task'));

      submitResult.className = 'form-result success';
      submitResult.textContent = `Task created successfully: ${data.id}`;

      submitForm.reset();
      updateScheduleState();
      resetSubmitFormLinks();

      skip = 0;
      fetchTasks();
      fetchStats();
    } catch (err) {
      submitResult.className = 'form-result error';
      submitResult.textContent = normalizeError(err, 'Failed to submit task');
    }
  });
}

if (taskEditForm) {
  taskEditForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (!currentTaskId) {
      if (taskEditResult) {
        taskEditResult.className = 'form-result error';
        taskEditResult.textContent = 'No task selected for editing.';
      }
      return;
    }

    if (taskEditResult) {
      taskEditResult.className = 'form-result';
      taskEditResult.textContent = 'Saving changes...';
    }

    try {
      const submissionPayload = collectTaskEditPayload();
      await executeTaskAction(`/tasks/${currentTaskId}`, 'PATCH', { submission: submissionPayload });

      if (taskEditResult) {
        taskEditResult.className = 'form-result success';
        taskEditResult.textContent = 'Task updated successfully.';
      }

      closeTaskEditModal();
      showTaskActionResult('Task updated successfully.');
      fetchTaskDetails(currentTaskId);
      fetchTasks();
      fetchStats();
    } catch (err) {
      if (taskEditResult) {
        taskEditResult.className = 'form-result error';
        taskEditResult.textContent = normalizeError(err, 'Failed to update task');
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
  li.className = 'item-card clickable-card';
  li.setAttribute('role', 'button');
  li.setAttribute('tabindex', '0');

  const active = !!credential.active;
  const status = active ? 'Active' : 'Inactive';
  const lastUsed = formatDate(credential.last_used_at);

  li.innerHTML = `
    <div>
      <strong>${escapeHtml(credential.name || credential.service || '-')}</strong>
      <div class="text-muted small">Service: ${escapeHtml(credential.service || '-')} | Key: ${escapeHtml(credential.key || '****')}</div>
      <div class="text-muted small">Created: ${formatDate(credential.created_at)} | Last Used: ${lastUsed}</div>
      <span class="task-status ${active ? 'status-success' : 'status-warning'}">${status}</span>
    </div>
    <div class="item-actions">
      <button type="button" class="btn btn-secondary btn-xs" data-action="edit">Edit</button>
      <button type="button" class="btn btn-secondary btn-xs" data-action="toggle">${active ? 'Deactivate' : 'Activate'}</button>
      <button type="button" class="btn btn-secondary btn-xs" data-action="delete">Delete</button>
    </div>
  `;

  li.querySelector('[data-action="edit"]')?.addEventListener('click', (event) => {
    event.stopPropagation();
    openCredentialModal(credential);
  });

  li.addEventListener('click', (event) => {
    if (event.target instanceof Element && event.target.closest('button, a, input, select, textarea, label')) {
      return;
    }
    openCredentialModal(credential);
  });

  li.addEventListener('keydown', (event) => {
    if (event.target instanceof Element && event.target.closest('button, a, input, select, textarea, label')) {
      return;
    }
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      openCredentialModal(credential);
    }
  });

  li.querySelector('[data-action="toggle"]')?.addEventListener('click', async (event) => {
    event.stopPropagation();
    try {
      const response = await fetch(`/settings/credentials/${credential.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active: !active }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseApiError(data, 'Failed to update credential'));

      if (credResult) {
        credResult.className = 'form-result success';
        credResult.textContent = 'Credential updated successfully.';
      }
      fetchCredentials();
    } catch (err) {
      if (credResult) {
        credResult.className = 'form-result error';
        credResult.textContent = normalizeError(err, 'Failed to update credential');
      }
    }
  });

  li.querySelector('[data-action="delete"]')?.addEventListener('click', async (event) => {
    event.stopPropagation();
    if (!confirm('Delete this credential?')) return;

    try {
      const response = await fetch(`/settings/credentials/${credential.id}`, { method: 'DELETE' });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(parseApiError(data, 'Failed to delete credential'));
      }
      if (editingCredentialId === credential.id) resetCredentialForm();
      if (credResult) {
        credResult.className = 'form-result success';
        credResult.textContent = 'Credential deleted successfully.';
      }
      fetchCredentials();
    } catch (err) {
      if (credResult) {
        credResult.className = 'form-result error';
        credResult.textContent = normalizeError(err, 'Failed to delete credential');
      }
    }
  });

  return li;
}

async function fetchCredentials() {
  if (!credList) return;

  credList.innerHTML = '<li class="loading">Loading...</li>';

  try {
    const response = await fetch('/settings/credentials');
    const items = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(items, 'Failed to load credentials'));

    credList.innerHTML = '';
    if (!Array.isArray(items) || items.length === 0) {
      credList.innerHTML = '<li class="empty-state">No credentials configured</li>';
      return;
    }

    items.forEach((item) => credList.appendChild(renderCredentialItem(item)));
  } catch (err) {
    credList.innerHTML = `<li class="empty-state">Error: ${escapeHtml(normalizeError(err, 'Failed to load credentials'))}</li>`;
  }
}

if (credForm) {
  credForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (credFormResult) {
      credFormResult.className = 'form-result';
      credFormResult.textContent = editingCredentialId ? 'Updating...' : 'Saving...';
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
          throw new Error('Service, Credential Name, and API Key are required.');
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
      if (!response.ok) throw new Error(parseApiError(data, 'Failed to save credential'));

      if (credResult) {
        credResult.className = 'form-result success';
        credResult.textContent = editingCredentialId ? 'Credential updated successfully.' : 'Credential saved successfully.';
      }
      resetCredentialForm();
      closeCredentialModal();
      fetchCredentials();
    } catch (err) {
      if (credFormResult) {
        credFormResult.className = 'form-result error';
        credFormResult.textContent = normalizeError(err, 'Failed to save credential');
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
  li.className = 'item-card clickable-card';
  li.setAttribute('role', 'button');
  li.setAttribute('tabindex', '0');

  const active = !!prompt.active;
  const shortSystem = (prompt.system_prompt || '').slice(0, 160);

  li.innerHTML = `
    <div>
      <strong>${escapeHtml(prompt.name || '-')}</strong>
      <div class="text-muted small">${escapeHtml(prompt.short_description || prompt.purpose || '')}</div>
      <div class="text-muted small">Purpose: ${escapeHtml(prompt.purpose || '-')} | Model: ${escapeHtml(prompt.model_id || '-')}</div>
      <div class="text-muted small">${escapeHtml(shortSystem)}${(prompt.system_prompt || '').length > 160 ? '...' : ''}</div>
      <span class="task-status ${active ? 'status-success' : 'status-warning'}">${active ? 'Active' : 'Inactive'}</span>
    </div>
    <div class="item-actions">
      <button type="button" class="btn btn-secondary btn-xs" data-action="edit">Edit</button>
      <button type="button" class="btn btn-secondary btn-xs" data-action="toggle">${active ? 'Deactivate' : 'Activate'}</button>
      <button type="button" class="btn btn-secondary btn-xs" data-action="delete">Delete</button>
    </div>
  `;

  li.querySelector('[data-action="edit"]')?.addEventListener('click', (event) => {
    event.stopPropagation();
    openPromptModal(prompt);
  });

  li.addEventListener('click', (event) => {
    if (event.target instanceof Element && event.target.closest('button, a, input, select, textarea, label')) {
      return;
    }
    openPromptModal(prompt);
  });

  li.addEventListener('keydown', (event) => {
    if (event.target instanceof Element && event.target.closest('button, a, input, select, textarea, label')) {
      return;
    }
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      openPromptModal(prompt);
    }
  });

  li.querySelector('[data-action="toggle"]')?.addEventListener('click', async (event) => {
    event.stopPropagation();
    try {
      const response = await fetch(`/settings/prompts/${prompt.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active: !active }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseApiError(data, 'Failed to update prompt'));

      if (promptResult) {
        promptResult.className = 'form-result success';
        promptResult.textContent = 'Prompt updated successfully.';
      }
      fetchPrompts();
    } catch (err) {
      if (promptResult) {
        promptResult.className = 'form-result error';
        promptResult.textContent = normalizeError(err, 'Failed to update prompt');
      }
    }
  });

  li.querySelector('[data-action="delete"]')?.addEventListener('click', async (event) => {
    event.stopPropagation();
    if (!confirm('Delete this prompt?')) return;

    try {
      const response = await fetch(`/settings/prompts/${prompt.id}`, { method: 'DELETE' });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(parseApiError(data, 'Failed to delete prompt'));
      }
      if (editingPromptId === prompt.id) resetPromptForm();
      if (promptResult) {
        promptResult.className = 'form-result success';
        promptResult.textContent = 'Prompt deleted successfully.';
      }
      fetchPrompts();
    } catch (err) {
      if (promptResult) {
        promptResult.className = 'form-result error';
        promptResult.textContent = normalizeError(err, 'Failed to delete prompt');
      }
    }
  });

  return li;
}

async function fetchPrompts() {
  if (!promptList) return;

  promptList.innerHTML = '<li class="loading">Loading...</li>';

  try {
    const response = await fetch('/settings/prompts');
    const items = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(items, 'Failed to load prompts'));

    promptList.innerHTML = '';
    if (!Array.isArray(items) || items.length === 0) {
      promptList.innerHTML = '<li class="empty-state">No prompts configured</li>';
      return;
    }

    items.forEach((item) => promptList.appendChild(renderPromptItem(item)));
  } catch (err) {
    promptList.innerHTML = `<li class="empty-state">Error: ${escapeHtml(normalizeError(err, 'Failed to load prompts'))}</li>`;
  }
}

if (promptForm) {
  promptForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (promptFormResult) {
      promptFormResult.className = 'form-result';
      promptFormResult.textContent = editingPromptId ? 'Updating...' : 'Saving...';
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
        throw new Error('Prompt name, purpose, system prompt, and user prompt are required.');
      }

      const response = await fetch(editingPromptId ? `/settings/prompts/${editingPromptId}` : '/settings/prompts', {
        method: editingPromptId ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseApiError(data, 'Failed to save prompt'));

      if (promptResult) {
        promptResult.className = 'form-result success';
        promptResult.textContent = editingPromptId ? 'Prompt updated successfully.' : 'Prompt saved successfully.';
      }
      resetPromptForm();
      closePromptModal();
      fetchPrompts();
    } catch (err) {
      if (promptFormResult) {
        promptFormResult.className = 'form-result error';
        promptFormResult.textContent = normalizeError(err, 'Failed to save prompt');
      }
    }
  });
}

function setPipelinesResult(message, isError = false) {
  if (!pipelinesResult) return;
  pipelinesResult.className = message ? `form-result ${isError ? 'error' : 'success'}` : 'form-result';
  pipelinesResult.textContent = message || '';
}

async function fetchPipelines() {
  if (!pipelinesGrid) return;
  setPipelinesResult('');
  pipelinesGrid.innerHTML = '<div class="loading">Loading pipelines...</div>';

  try {
    const response = await fetch('/settings/pipelines');
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(data, 'Failed to load pipelines'));

    pipelinesGrid.innerHTML = '';
    if (!Array.isArray(data) || data.length === 0) {
      pipelinesGrid.innerHTML = '<div class="empty-state">No pipelines configured</div>';
      return;
    }

    data.forEach((pipeline) => {
      const card = document.createElement('article');
      card.className = 'pipeline-card clickable-card';
      card.setAttribute('role', 'button');
      card.setAttribute('tabindex', '0');
      card.innerHTML = `
        <h3>${escapeHtml(pipeline.name || '-')}</h3>
        <p class="text-muted">${escapeHtml(pipeline.description || '')}</p>
        <div class="pipeline-card-meta">
          <span><strong>Usage Type:</strong> ${escapeHtml(pipeline.usage_type || '-')}</span>
          <span><strong>Version:</strong> ${escapeHtml(pipeline.version || '-')}</span>
          <span><strong>Steps:</strong> ${escapeHtml(pipeline.steps_count || 0)}</span>
          <span><strong>AI Steps:</strong> ${escapeHtml(pipeline.ai_steps_count || 0)}</span>
        </div>
        <div class="pipeline-card-actions">
          <button type="button" class="btn btn-primary">Configure</button>
        </div>
      `;

      const openPipelineDetails = () => {
        fetchPipelineDetails(String(pipeline.id || ''));
        if (pipelineDetailsContent) {
          pipelineDetailsContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      };

      card.addEventListener('click', (event) => {
        if (event.target instanceof Element && event.target.closest('button, a, input, select, textarea, label')) {
          return;
        }
        openPipelineDetails();
      });

      card.addEventListener('keydown', (event) => {
        if (event.target instanceof Element && event.target.closest('button, a, input, select, textarea, label')) {
          return;
        }
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          openPipelineDetails();
        }
      });

      card.querySelector('button')?.addEventListener('click', (event) => {
        event.stopPropagation();
        openPipelineDetails();
      });
      pipelinesGrid.appendChild(card);
    });
  } catch (err) {
    const message = normalizeError(err, 'Failed to load pipelines');
    pipelinesGrid.innerHTML = `<div class="empty-state">Error: ${escapeHtml(message)}</div>`;
    setPipelinesResult(message, true);
  }
}

function renderPipelineDetails(details) {
  if (!pipelineDetailsContent) return;
  const steps = Array.isArray(details?.steps) ? details.steps : [];
  const availableCredentials = Array.isArray(details?.available_credentials) ? details.available_credentials : [];
  const availablePrompts = Array.isArray(details?.available_prompts) ? details.available_prompts : [];

  if (pipelineDetailsTitle) {
    pipelineDetailsTitle.textContent = `Pipeline: ${details?.name || '-'}`;
  }

  const stepsHtml = steps
    .map((step) => {
      const ai = step?.ai || {};
      const provider = String(ai.provider || '').toLowerCase();
      const preferredCredentials = availableCredentials.filter(
        (item) => String(item.service || '').toLowerCase() === provider
      );
      const credentialOptions = (preferredCredentials.length ? preferredCredentials : availableCredentials)
        .map((item) => {
          const selected = ai.credential_id && ai.credential_id === item.id ? 'selected' : '';
          const label = `${item.name || '-'} (${item.service || '-'})`;
          return `<option value="${escapeHtml(item.id)}" ${selected}>${escapeHtml(label)}</option>`;
        })
        .join('');

      const promptOptions = availablePrompts
        .map((item) => {
          const selected = ai.prompt_id && ai.prompt_id === item.id ? 'selected' : '';
          const label = `${item.name || '-'}${item.purpose ? ` (${item.purpose})` : ''}`;
          return `<option value="${escapeHtml(item.id)}" ${selected}>${escapeHtml(label)}</option>`;
        })
        .join('');

      const credentialDefaultLabel = ai.default_credential_name
        ? `Default (${ai.default_credential_name})`
        : 'No credential defined';
      const promptDefaultLabel = ai.default_prompt_purpose
        ? `Default (${ai.default_prompt_purpose})`
        : 'No default prompt';

      return `
        <article class="pipeline-step-card">
          <div class="pipeline-step-header">
            <h4>${escapeHtml(step.name || step.id || '-')}</h4>
            <span class="task-status ${step.uses_ai ? 'status-info' : 'status-warning'}">${step.uses_ai ? 'AI' : 'System'}</span>
          </div>
          <p class="text-muted">${escapeHtml(step.description || '')}</p>
          <div class="pipeline-step-meta">
            <span><strong>ID:</strong> ${escapeHtml(step.id || '-')}</span>
            <span><strong>Usage Type:</strong> ${escapeHtml(step.type || '-')}</span>
          </div>
          ${
            step.uses_ai
              ? `
            <div class="pipeline-ai-panel">
              <div class="pipeline-step-meta">
                <span><strong>Provider:</strong> ${escapeHtml(ai.provider || '-')}</span>
                <span><strong>Model:</strong> ${escapeHtml(ai.model_id || '-')}</span>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">Credential</label>
                  <select class="form-input pipeline-credential-select" data-step-id="${escapeHtml(step.id)}">
                    <option value="">${escapeHtml(credentialDefaultLabel)}</option>
                    ${credentialOptions}
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">Prompt</label>
                  <select class="form-input pipeline-prompt-select" data-step-id="${escapeHtml(step.id)}">
                    <option value="">${escapeHtml(promptDefaultLabel)}</option>
                    ${promptOptions}
                  </select>
                </div>
              </div>
              <div class="task-actions">
                <button type="button" class="btn btn-primary pipeline-step-save-btn" data-step-id="${escapeHtml(step.id)}">Save Configuration</button>
              </div>
            </div>
          `
              : ''
          }
        </article>
      `;
    })
    .join('');

  pipelineDetailsContent.innerHTML = `
    <div class="pipeline-detail-meta">
      <div><strong>Slug:</strong> ${escapeHtml(details?.slug || '-')}</div>
      <div><strong>Usage Type:</strong> ${escapeHtml(details?.usage_type || '-')}</div>
      <div><strong>Version:</strong> ${escapeHtml(details?.version || '-')}</div>
    </div>
    <p class="text-muted">${escapeHtml(details?.description || '')}</p>
    <div class="pipeline-steps-list">
      ${stepsHtml}
    </div>
  `;
}

function wirePipelineDetailsActions(pipelineId) {
  const saveButtons = document.querySelectorAll('.pipeline-step-save-btn');
  saveButtons.forEach((button) => {
    button.addEventListener('click', async () => {
      const stepId = button.dataset.stepId;
      if (!stepId) return;

      const row = button.closest('.pipeline-step-card');
      const credentialSelect = row?.querySelector('.pipeline-credential-select');
      const promptSelect = row?.querySelector('.pipeline-prompt-select');

      const payload = {
        credential_id: credentialSelect?.value ? String(credentialSelect.value) : null,
        prompt_id: promptSelect?.value ? String(promptSelect.value) : null,
      };

      try {
        button.disabled = true;
        setPipelinesResult('Saving configuration...');

        const response = await fetch(`/settings/pipelines/${pipelineId}/steps/${stepId}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(parseApiError(data, 'Failed to save step configuration'));

        setPipelinesResult('Pipeline configuration updated successfully.');
        await fetchPipelineDetails(pipelineId, { silent: true });
      } catch (err) {
        setPipelinesResult(normalizeError(err, 'Failed to save step configuration'), true);
      } finally {
        button.disabled = false;
      }
    });
  });
}

async function fetchPipelineDetails(pipelineId, options = {}) {
  const silent = !!options.silent;
  if (!pipelineId || !pipelineDetailsContent) return;

  currentPipelineId = pipelineId;
  if (!silent) pipelineDetailsContent.innerHTML = '<div class="loading">Loading pipeline details...</div>';

  try {
    const response = await fetch(`/settings/pipelines/${pipelineId}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(data, 'Failed to load details da pipeline'));

    currentPipelineDetails = data;
    renderPipelineDetails(data);
    wirePipelineDetailsActions(pipelineId);
  } catch (err) {
    pipelineDetailsContent.innerHTML = `<div class="form-result error">Error: ${escapeHtml(normalizeError(err, 'Failed to load details da pipeline'))}</div>`;
  }
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

if (backToTasksBtn) {
  backToTasksBtn.addEventListener('click', () => {
    showSection('tasks-section');
  });
}

if (sidebarToggleBtn) {
  sidebarToggleBtn.addEventListener('click', () => {
    const collapsed = !layoutEl?.classList.contains('sidebar-collapsed');
    applySidebarCollapsedState(collapsed);
    persistSidebarCollapsedState(collapsed);
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
  applySidebarCollapsedState(readSidebarCollapsedState());
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
  fetchPipelines();
});
