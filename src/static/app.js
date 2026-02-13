const navLinks = document.querySelectorAll('.nav-link');
const sections = document.querySelectorAll('.section');

const submitForm = document.getElementById('submit-form');
const submitResult = document.getElementById('submit-result');
const submitSectionTitle = document.getElementById('submit-section-title');
const submitTaskBtn = document.getElementById('submit-task-btn');
const cancelEditTaskBtn = document.getElementById('cancel-edit-task-btn');

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
const promptCategoryInput = document.getElementById('prompt-category');
const promptProviderInput = document.getElementById('prompt-provider');
const promptFilterCategoryInput = document.getElementById('prompt-filter-category');
const promptFilterProviderInput = document.getElementById('prompt-filter-provider');
const promptFilterNameInput = document.getElementById('prompt-filter-name');
const createPromptBtn = document.getElementById('create-prompt-btn');
const promptModal = document.getElementById('prompt-modal');
const promptModalTitle = document.getElementById('prompt-modal-title');
const promptCancelBtn = document.getElementById('prompt-cancel-btn');

const contentSchemaForm = document.getElementById('content-schema-form');
const contentSchemaResult = document.getElementById('content-schema-result');
const contentSchemaFormResult = document.getElementById('content-schema-form-result');
const contentSchemaList = document.getElementById('content-schema-list');
const createContentSchemaBtn = document.getElementById('create-content-schema-btn');
const contentSchemaEditorPanel = document.getElementById('content-schema-editor-panel');
const contentSchemaModalTitle = document.getElementById('content-schema-modal-title');
const contentSchemaCancelBtn = document.getElementById('content-schema-cancel-btn');
const tocItemsContainer = document.getElementById('toc-items-container');
const addTocItemBtn = document.getElementById('add-toc-item-btn');

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
const mainCategoryInput = document.getElementById('main_category');
const mainCategoryCredentialInput = document.getElementById('main_category_credential');
const contentSchemaInput = document.getElementById('content_schema_id');

let skip = 0;
const limit = 10;
let currentTaskId = null;
let currentTaskDetails = null;
let editingTaskId = null;
let editingTaskBaseSubmission = null;
let searchDebounceTimer = null;
let promptSearchDebounceTimer = null;
let editingCredentialId = null;
let editingPromptId = null;
let editingContentSchemaId = null;
let currentPipelineId = null;
let currentPipelineDetails = null;
let cachedPromptOptions = [];
let cachedPromptCategories = [];
const WP_CREDENTIAL_STORAGE_KEY = 'pigmeu.bookReview.wordpressCredentialId';
const DEFAULT_WORDPRESS_CREDENTIAL_URL = 'https://analisederequisitos.com.br';
const SIDEBAR_STORAGE_KEY = 'pigmeu.sidebar.collapsed';
const PROMPT_DEFAULT_CATEGORY = 'Book Review';
const PROMPT_DEFAULT_PROVIDER = 'groq';
const PROMPT_DEFAULT_MODEL = 'llama-3.3-70b-versatile';
const PROMPT_PROVIDER_OPTIONS = [
  { value: 'groq', label: 'Groq' },
  { value: 'mistral', label: 'Mistral' },
];

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

function getActionIconSvg(action) {
  const icons = {
    edit: `
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M12 20h9"></path>
        <path d="M16.5 3.5a2.12 2.12 0 1 1 3 3L7 19l-4 1 1-4 12.5-12.5z"></path>
      </svg>
    `,
    delete: `
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M3 6h18"></path>
        <path d="M8 6V4h8v2"></path>
        <path d="M19 6l-1 14H6L5 6"></path>
        <path d="M10 11v6"></path>
        <path d="M14 11v6"></path>
      </svg>
    `,
    toggle: `
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M12 2v10"></path>
        <path d="M5.6 5.6a9 9 0 1 0 12.8 0"></path>
      </svg>
    `,
    configure: `
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M4 21v-7"></path>
        <path d="M4 10V3"></path>
        <path d="M12 21v-9"></path>
        <path d="M12 8V3"></path>
        <path d="M20 21v-5"></path>
        <path d="M20 12V3"></path>
        <circle cx="4" cy="12" r="2"></circle>
        <circle cx="12" cy="10" r="2"></circle>
        <circle cx="20" cy="14" r="2"></circle>
      </svg>
    `,
    save: `
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M5 3h12l4 4v14H5z"></path>
        <path d="M8 3v6h8V3"></path>
        <path d="M9 21v-6h6v6"></path>
      </svg>
    `,
    view: `
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6z"></path>
        <circle cx="12" cy="12" r="3"></circle>
      </svg>
    `,
    generate: `
      <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
        <path d="M5 3v18l15-9-15-9z"></path>
      </svg>
    `,
  };
  return icons[action] || icons.configure;
}

function renderIconActionContent(action, label) {
  const safeLabel = escapeHtml(label || action || 'action');
  return `${getActionIconSvg(action)}<span class="sr-only">${safeLabel}</span>`;
}

function setIconButtonContent(button, action, label) {
  if (!button) return;
  button.classList.add('btn-icon-only');
  button.innerHTML = renderIconActionContent(action, label);
  button.setAttribute('aria-label', label);
  button.setAttribute('title', label);
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

  if (sectionId === 'content-schemas-section') {
    fetchContentSchemas();
  }

  if (sectionId === 'submit-section') {
    initializeMainCategorySources();
    initializeContentSchemaOptions();
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

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  fetchTasks();
  fetchStats();
  applyStaticActionIcons();
  const collapsed = readSidebarCollapsedState();
  applySidebarCollapsedState(collapsed);
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

function applyStaticActionIcons() {
  const credentialSaveBtn = document.getElementById('credential-save-btn');
  const promptSaveBtn = document.getElementById('prompt-save-btn');
  const taskEditSaveBtn = document.querySelector('#task-edit-form button[type="submit"]');

  setIconButtonContent(credentialSaveBtn, 'save', 'Save credential');
  setIconButtonContent(promptSaveBtn, 'save', 'Save prompt');
  setIconButtonContent(taskEditSaveBtn, 'save', 'Save task changes');
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
  const hasFinalArticle =
    !!task.article_id ||
    ['article_generated', 'ready_for_review', 'approved', 'published'].includes(
      String(task.status || '').toLowerCase()
    );

  card.innerHTML = `
    <h3>${escapeHtml(task.title || '-')}</h3>
    <p><strong>${escapeHtml(task.author_name || '-')}</strong></p>
    <p class="text-muted">${shortUrl}</p>
    <div class="task-card-footer">
      <span class="task-status ${statusClass(task.status)}">${escapeHtml(statusLabel(task.status))}</span>
      <div class="task-card-meta-actions">
        <span class="text-muted small">${formatDate(task.updated_at)}</span>
        <button
          type="button"
          class="btn btn-secondary btn-xs btn-icon-only task-card-view-article-btn"
          aria-label="View final article"
          title="View final article"
          ${hasFinalArticle ? '' : 'disabled'}
        >
          ${renderIconActionContent('view', 'View final article')}
        </button>
        <button
          type="button"
          class="btn btn-danger btn-xs btn-icon-only task-card-delete-btn"
          aria-label="Delete task"
          title="Delete task"
        >
          ${renderIconActionContent('delete', 'Delete task')}
        </button>
      </div>
    </div>
  `;

  const deleteBtn = card.querySelector('.task-card-delete-btn');
  const viewArticleBtn = card.querySelector('.task-card-view-article-btn');

  const openDetails = (focusArticle = false) => {
    currentTaskId = task.id;
    showSection('task-details-section');
    fetchTaskDetails(task.id, { focusArticle });
  };

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

  if (viewArticleBtn) {
    viewArticleBtn.addEventListener('click', (event) => {
      event.stopPropagation();
      openDetails(true);
    });
  }

  card.addEventListener('click', () => {
    openDetails(false);
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

const DEFAULT_TASK_FLOW_DEFINITION = [
  { id: 'amazon_scrape', label: 'Amazon link scrap' },
  { id: 'additional_links_scrape', label: 'Additional links scrap' },
  { id: 'summarize_additional_links', label: 'Summarize additional links' },
  { id: 'consolidate_book_data', label: 'Consolidate book data' },
  { id: 'internet_research', label: 'Internet research' },
  { id: 'context_generation', label: 'Generate context' },
  { id: 'article_generation', label: 'Generate article' },
  { id: 'ready_for_review', label: 'Ready for review' },
];

function humanizeStepId(stepId) {
  return String(stepId || '')
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function resolveTaskFlowDefinition(taskData = null) {
  const pipelineSteps = Array.isArray(taskData?.pipeline?.steps) ? taskData.pipeline.steps : [];
  if (!pipelineSteps.length) return DEFAULT_TASK_FLOW_DEFINITION;

  const normalized = pipelineSteps
    .map((step) => {
      const id = String(step?.id || '').trim();
      if (!id) return null;
      const label = String(step?.name || '').trim() || humanizeStepId(id);
      return { id, label };
    })
    .filter(Boolean);

  return normalized.length ? normalized : DEFAULT_TASK_FLOW_DEFINITION;
}

function mapCurrentTaskStep(submission = {}, flowDefinition = DEFAULT_TASK_FLOW_DEFINITION) {
  const flowIds = new Set(flowDefinition.map((step) => String(step.id || '').toLowerCase()));
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
    if (!raw) continue;

    const mapped = String(map[raw] || raw).toLowerCase();
    if (flowIds.has(mapped)) return mapped;

    if (raw.includes('context')) {
      const byContext = flowDefinition.find((step) => String(step.id || '').toLowerCase().includes('context'));
      if (byContext) return byContext.id;
    }
    if (raw.includes('article') || raw.includes('review')) {
      const byArticle = flowDefinition.find((step) => String(step.id || '').toLowerCase().includes('article'));
      if (byArticle) return byArticle.id;
    }
    if (raw.includes('scrap')) {
      const byScrape = flowDefinition.find((step) => String(step.id || '').toLowerCase().includes('scrap'));
      if (byScrape) return byScrape.id;
    }
  }
  return null;
}

function buildTaskFlowSteps(taskData) {
  const flowDefinition = resolveTaskFlowDefinition(taskData);
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
  flowDefinition.forEach((step) => {
    states[step.id] = 'to_do';
  });

  if (hasAmazonData && states.amazon_scrape !== undefined) states.amazon_scrape = 'processed';
  if (hasLinksStep && states.additional_links_scrape !== undefined) states.additional_links_scrape = 'processed';
  if (hasSummaryStep && states.summarize_additional_links !== undefined) states.summarize_additional_links = 'processed';
  if (hasConsolidated && states.consolidate_book_data !== undefined) states.consolidate_book_data = 'processed';
  if (hasResearch && states.internet_research !== undefined) states.internet_research = 'processed';
  if (hasContext && states.context_generation !== undefined) states.context_generation = 'processed';
  if (hasArticle && states.article_generation !== undefined) states.article_generation = 'processed';
  if (isReady && states.ready_for_review !== undefined) states.ready_for_review = 'processed';

  const currentStep = mapCurrentTaskStep(submission, flowDefinition);
  const currentIndex = flowDefinition.findIndex((step) => step.id === currentStep);
  const isFailed = ['scraping_failed', 'failed'].includes(status);

  if (currentIndex >= 0) {
    for (let i = 0; i < currentIndex; i += 1) {
      const prevId = flowDefinition[i].id;
      if (states[prevId] === 'to_do') states[prevId] = 'processed';
    }

    // If the pipeline is executing/retrying from a given step, all next steps must return to To Do.
    for (let i = currentIndex + 1; i < flowDefinition.length; i += 1) {
      states[flowDefinition[i].id] = 'to_do';
    }
  }

  if (isFailed && currentStep) {
    states[currentStep] = 'failed';
  } else if (currentStep && states[currentStep] === 'to_do') {
    states[currentStep] = 'current';
  }

  return flowDefinition.map((step) => ({
    ...step,
    state: states[step.id] || 'to_do',
  }));
}

function getFlowStatusLabel(state) {
  if (state === 'processed') return 'Processed';
  if (state === 'failed') return 'Failed';
  if (state === 'current') return 'Current';
  return 'To Do';
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
                  Retry
                </button>
                <button type="button" class="btn btn-secondary btn-xs step-action-view" data-step-stage="${escapeHtml(step.id)}" ${canView ? '' : 'disabled'}>
                  View Content
                </button>
              </div>
            </div>
          `;
        })
        .join('')}
    </div>
  `;
}

function buildFlowStepsAfterRetry(taskData, retryStage) {
  const flowSteps = buildTaskFlowSteps(taskData).map((step) => ({ ...step }));
  const retryIndex = flowSteps.findIndex((step) => step.id === retryStage);
  if (retryIndex < 0) return flowSteps;

  flowSteps.forEach((step, idx) => {
    if (idx > retryIndex) step.state = 'to_do';
  });

  if (flowSteps[retryIndex]) {
    flowSteps[retryIndex].state = 'current';
  }

  return flowSteps;
}

function getFinalArticleContent(taskData) {
  const article = taskData?.article || {};
  const draft = taskData?.draft || {};
  const content = String(article.content || draft.content || '').trim();
  if (!content) return null;

  return {
    title: String(article.title || taskData?.submission?.title || 'Generated Article'),
    content,
  };
}

function canGenerateArticleManually(taskData) {
  const submission = taskData?.submission || {};
  const status = String(submission.status || '').toLowerCase();
  const blockedStatuses = ['pending_article', 'article_generation'];
  if (blockedStatuses.includes(status)) return false;

  const article = taskData?.article || {};
  const draft = taskData?.draft || {};
  const hasArticle =
    !!taskData?.article?.id ||
    !!String(article.content || '').trim() ||
    !!String(draft.content || '').trim();
  if (hasArticle) return false;

  const hasContext = !!String(taskData?.knowledge_base?.markdown_content || '').trim();
  return hasContext;
}

function renderFinalArticleInViewer(taskData) {
  const viewer = document.getElementById('step-content-viewer');
  if (!viewer) return false;

  viewer.style.display = 'block';
  const articleContent = getFinalArticleContent(taskData);
  if (!articleContent) {
    viewer.innerHTML = `
      <h5>Final Article</h5>
      <p class="text-muted">Final article content is not available yet.</p>
    `;
    return false;
  }

  viewer.innerHTML = `
    <h5>Final Article: ${escapeHtml(articleContent.title)}</h5>
    <div class="article-preview">${markdownToHtml(articleContent.content)}</div>
  `;
  return true;
}

function renderTaskDetails(data, flowStepsOverride = null) {
  const submission = data.submission || {};
  const pipeline = data.pipeline || null;
  const allowManualGenerateArticle = canGenerateArticleManually(data);
  const flowSteps =
    Array.isArray(flowStepsOverride) && flowStepsOverride.length > 0
      ? flowStepsOverride
      : buildTaskFlowSteps(data);

  return `
    <div class="task-details-container">
      <div class="task-details-top">
        <h3 class="task-details-title">Task Details: ${escapeHtml(pipeline?.name || 'Book Review')}</h3>
        <div class="task-details-top-actions">
          ${
            allowManualGenerateArticle
              ? `
          <button id="action-generate-article" class="btn btn-primary btn-icon-only" type="button" aria-label="Generate article" title="Generate article">
            ${renderIconActionContent('generate', 'Generate article')}
          </button>
          `
              : ''
          }
          <button id="action-view-final-article" class="btn btn-secondary btn-icon-only" type="button" aria-label="View final article" title="View final article">
            ${renderIconActionContent('view', 'View final article')}
          </button>
          <button id="action-edit-task" class="btn btn-primary btn-icon-only" type="button" aria-label="Edit task" title="Edit task">
            ${renderIconActionContent('edit', 'Edit task')}
          </button>
          <button id="action-delete-task" class="btn btn-danger btn-icon-only" type="button" aria-label="Delete task" title="Delete task">
            ${renderIconActionContent('delete', 'Delete task')}
          </button>
        </div>
      </div>
      <div class="task-details-divider"></div>

      <div class="task-meta-grid">
        <div class="task-meta-col">
          <p class="task-meta-line"><strong>Book:</strong> ${escapeHtml(submission.title || '-')}</p>
          <p class="task-meta-line"><strong>Created:</strong> ${formatDate(submission.created_at)}</p>
        </div>
        <div class="task-meta-col">
          <p class="task-meta-line"><strong>Author:</strong> ${escapeHtml(submission.author_name || '-')}</p>
          <p class="task-meta-line"><strong>Last Update:</strong> ${formatDate(submission.updated_at)}</p>
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
  const generateArticleBtn = document.getElementById('action-generate-article');
  const viewFinalArticleBtn = document.getElementById('action-view-final-article');
  const editTaskBtn = document.getElementById('action-edit-task');
  const deleteTaskBtn = document.getElementById('action-delete-task');
  const stepContentViewer = document.getElementById('step-content-viewer');
  const reprocessButtons = document.querySelectorAll('.step-action-reprocess');
  const viewButtons = document.querySelectorAll('.step-action-view');

  if (generateArticleBtn) {
    generateArticleBtn.addEventListener('click', async () => {
      try {
        generateArticleBtn.disabled = true;
        await executeTaskAction(`/tasks/${taskId}/generate_article`, 'POST');
        showTaskActionResult('Article generation queued successfully.');
        setTimeout(() => fetchTaskDetails(taskId), 1000);
      } catch (err) {
        showTaskActionResult(normalizeError(err, 'Failed to queue article generation'), true);
      } finally {
        generateArticleBtn.disabled = false;
      }
    });
  }

  if (viewFinalArticleBtn) {
    viewFinalArticleBtn.addEventListener('click', () => {
      const displayed = renderFinalArticleInViewer(taskData);
      if (!displayed) {
        showTaskActionResult('Final article content is not available yet.', true);
      }
    });
  }

  if (editTaskBtn) {
    editTaskBtn.addEventListener('click', () => {
      openTaskEditOnSubmitForm(taskId, taskData?.submission || {});
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
        `Retrying step "${stepLabel}" will discard all later completed steps and run them again.\n\nDo you want to continue?`
      );
      if (!confirmed) return;

      try {
        button.disabled = true;
        await executeTaskAction(config.url, config.method || 'POST', config.payload || null);

        // Optimistic UI update: keep retried step as current and reset all next steps to To Do.
        const flowStepsAfterRetry = buildFlowStepsAfterRetry(taskData, stage);
        setTaskDetailsContent(renderTaskDetails(taskData, flowStepsAfterRetry));
        wireTaskActions(taskId, taskData);

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

async function fetchTaskDetails(taskId, options = {}) {
  const focusArticle = !!options.focusArticle;
  setTaskDetailsContent('<div class="loading">Loading details...</div>');

  try {
    const response = await fetch(`/tasks/${taskId}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(data, 'Failed to load task details'));

    currentTaskDetails = data;
    setTaskDetailsContent(renderTaskDetails(data));
    wireTaskActions(taskId, data);
    if (focusArticle) {
      const displayed = renderFinalArticleInViewer(data);
      if (!displayed) {
        showTaskActionResult('Final article content is not available yet.', true);
      }
    }
    return data;
  } catch (err) {
    setTaskDetailsContent(`<div class="form-result error">Error: ${escapeHtml(normalizeError(err, 'Failed to load details'))}</div>`);
    return null;
  }
}

function updateScheduleState() {
  if (!runImmediatelyInput || !scheduleInput) return;
  const runNow = runImmediatelyInput.checked;
  scheduleInput.disabled = runNow;
  scheduleInput.required = !runNow;
  if (runNow) scheduleInput.value = '';
}

function setSubmitFormMode(editing) {
  if (submitSectionTitle) {
    submitSectionTitle.textContent = editing ? 'Edit Task: Book Review Article' : 'New Task: Book Review Article';
  }
  if (submitTaskBtn) {
    if (editing) {
      setIconButtonContent(submitTaskBtn, 'save', 'Save task changes');
    } else {
      submitTaskBtn.classList.remove('btn-icon-only');
      submitTaskBtn.textContent = 'Create Task';
      submitTaskBtn.setAttribute('aria-label', 'Create task');
      submitTaskBtn.setAttribute('title', 'Create task');
    }
  }
  if (cancelEditTaskBtn) {
    cancelEditTaskBtn.style.display = editing ? 'inline-flex' : 'none';
  }
}

function clearSubmitEditMode() {
  editingTaskId = null;
  editingTaskBaseSubmission = null;
  setSubmitFormMode(false);
}

function readStoredWordpressCredentialId() {
  try {
    return localStorage.getItem(WP_CREDENTIAL_STORAGE_KEY) || '';
  } catch (_) {
    return '';
  }
}

function storeWordpressCredentialId(credentialId) {
  try {
    if (credentialId) {
      localStorage.setItem(WP_CREDENTIAL_STORAGE_KEY, String(credentialId));
    } else {
      localStorage.removeItem(WP_CREDENTIAL_STORAGE_KEY);
    }
  } catch (_) {
    // no-op
  }
}

function applyMainCategorySelection(value) {
  if (!mainCategoryInput) return;
  const normalized = String(value || '').trim();
  if (!normalized) {
    mainCategoryInput.value = '';
    mainCategoryInput.dataset.pendingValue = '';
    return;
  }

  const existing = Array.from(mainCategoryInput.options).find((opt) => opt.value === normalized);
  if (!existing) {
    const option = document.createElement('option');
    option.value = normalized;
    option.textContent = normalized;
    option.dataset.dynamic = 'true';
    mainCategoryInput.appendChild(option);
  }

  mainCategoryInput.value = normalized;
  mainCategoryInput.dataset.pendingValue = normalized;
}

function populateWordpressCredentialOptions(items = []) {
  if (!mainCategoryCredentialInput) return '';

  const credentials = Array.isArray(items) ? items : [];
  mainCategoryCredentialInput.innerHTML = '';

  if (credentials.length === 0) {
    mainCategoryCredentialInput.innerHTML = '<option value="">No active WordPress credential</option>';
    mainCategoryCredentialInput.disabled = true;
    return '';
  }

  mainCategoryCredentialInput.disabled = false;
  const storedId = readStoredWordpressCredentialId();
  const normalizedDefaultUrl = DEFAULT_WORDPRESS_CREDENTIAL_URL.replace(/\/$/, '').toLowerCase();
  const byStored = credentials.find((item) => String(item.id) === String(storedId));
  const byDefaultUrl = credentials.find((item) => {
    const url = String(item.url || '').replace(/\/$/, '').toLowerCase();
    return url && url === normalizedDefaultUrl;
  });
  const selected = byStored || byDefaultUrl || credentials[0];

  credentials.forEach((item) => {
    const option = document.createElement('option');
    option.value = String(item.id || '');
    option.textContent = item.url
      ? `${item.name || 'WordPress'} (${item.url})`
      : `${item.name || 'WordPress'} (${item.service || 'wordpress'})`;
    option.selected = String(item.id) === String(selected?.id || '');
    mainCategoryCredentialInput.appendChild(option);
  });

  return String(selected?.id || '');
}

function setMainCategoryLoading(message = 'Loading categories...') {
  if (!mainCategoryInput) return;
  const pendingValue = mainCategoryInput.dataset.pendingValue || '';
  mainCategoryInput.innerHTML = `<option value="">${escapeHtml(message)}</option>`;
  mainCategoryInput.disabled = true;
  if (pendingValue) applyMainCategorySelection(pendingValue);
}

function populateMainCategoryOptions(categories = []) {
  if (!mainCategoryInput) return;

  const pendingValue = mainCategoryInput.dataset.pendingValue || '';
  const items = Array.isArray(categories) ? categories : [];
  mainCategoryInput.innerHTML = '<option value="">Select category</option>';

  items.forEach((item) => {
    const name = String(item?.name || '').trim();
    if (!name) return;
    const option = document.createElement('option');
    option.value = name;
    option.textContent = name;
    mainCategoryInput.appendChild(option);
  });

  mainCategoryInput.disabled = false;
  if (pendingValue) {
    applyMainCategorySelection(pendingValue);
  }
}

async function fetchMainCategoriesByCredential(credentialId) {
  if (!credentialId) {
    setMainCategoryLoading('Select credential first');
    return;
  }

  setMainCategoryLoading();

  const params = new URLSearchParams({ credential_id: String(credentialId) });
  const response = await fetch(`/settings/wordpress/categories?${params.toString()}`);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(parseApiError(data, 'Failed to load WordPress categories'));
  }

  const categories = Array.isArray(data.categories) ? data.categories : [];
  populateMainCategoryOptions(categories);
}

async function initializeMainCategorySources() {
  if (!mainCategoryCredentialInput || !mainCategoryInput) return;

  try {
    const response = await fetch('/settings/credentials?service=wordpress&active=true');
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(data, 'Failed to load WordPress credentials'));

    const selectedCredentialId = populateWordpressCredentialOptions(data);
    if (!selectedCredentialId) {
      setMainCategoryLoading('No category available');
      return;
    }

    mainCategoryCredentialInput.value = selectedCredentialId;
    storeWordpressCredentialId(selectedCredentialId);
    await fetchMainCategoriesByCredential(selectedCredentialId);
  } catch (err) {
    if (mainCategoryCredentialInput) {
      mainCategoryCredentialInput.innerHTML = '<option value="">Error loading credentials</option>';
      mainCategoryCredentialInput.disabled = true;
    }
    setMainCategoryLoading(normalizeError(err, 'Error loading categories'));
  }
}

function applyContentSchemaSelection(value) {
  if (!contentSchemaInput) return;
  const normalized = String(value || '').trim();
  if (!normalized) {
    contentSchemaInput.value = '';
    contentSchemaInput.dataset.pendingValue = '';
    return;
  }

  const existing = Array.from(contentSchemaInput.options).find((opt) => opt.value === normalized);
  if (!existing) {
    const option = document.createElement('option');
    option.value = normalized;
    option.textContent = normalized;
    option.dataset.dynamic = 'true';
    contentSchemaInput.appendChild(option);
  }

  contentSchemaInput.value = normalized;
  contentSchemaInput.dataset.pendingValue = normalized;
}

function setContentSchemaLoading(message = 'Loading schemas...') {
  if (!contentSchemaInput) return;
  const pendingValue = contentSchemaInput.dataset.pendingValue || '';
  contentSchemaInput.innerHTML = `<option value="">${escapeHtml(message)}</option>`;
  contentSchemaInput.disabled = true;
  if (pendingValue) applyContentSchemaSelection(pendingValue);
}

function populateContentSchemaOptions(items = []) {
  if (!contentSchemaInput) return '';

  const schemas = Array.isArray(items) ? items : [];
  const pendingValue = contentSchemaInput.dataset.pendingValue || '';
  contentSchemaInput.innerHTML = '<option value="">Select content schema</option>';

  schemas.forEach((schema) => {
    const id = String(schema?.id || '').trim();
    if (!id) return;
    const option = document.createElement('option');
    option.value = id;
    option.textContent = schema?.name ? String(schema.name) : id;
    contentSchemaInput.appendChild(option);
  });

  if (schemas.length === 0) {
    contentSchemaInput.innerHTML = '<option value="">No active content schema</option>';
    contentSchemaInput.disabled = true;
    contentSchemaInput.dataset.pendingValue = '';
    return '';
  }

  const selectedId = pendingValue && schemas.some((item) => String(item?.id) === pendingValue)
    ? pendingValue
    : String(schemas[0]?.id || '');
  contentSchemaInput.value = selectedId;
  contentSchemaInput.dataset.pendingValue = selectedId;
  contentSchemaInput.disabled = false;
  return selectedId;
}

async function initializeContentSchemaOptions() {
  if (!contentSchemaInput) return;

  setContentSchemaLoading();
  try {
    const params = new URLSearchParams({
      active: 'true',
      target_type: 'book_review',
    });
    const response = await fetch(`/settings/content-schemas?${params.toString()}`);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(data, 'Failed to load content schemas'));

    populateContentSchemaOptions(Array.isArray(data) ? data : []);
  } catch (err) {
    setContentSchemaLoading(normalizeError(err, 'Error loading content schemas'));
  }
}

function readSubmitOtherLinks() {
  if (!otherLinksContainer) return [];
  return Array.from(otherLinksContainer.querySelectorAll('.other-link'))
    .map((input) => input.value.trim())
    .filter((url) => url);
}

function fillSubmitFormFromSubmission(submission = {}) {
  const titleInput = document.getElementById('title');
  const authorInput = document.getElementById('author_name');
  const amazonInput = document.getElementById('amazon_url');
  const textualInfoInput = document.getElementById('textual_information');
  const articleStatusInput = document.getElementById('article_status');
  const userApprovalInput = document.getElementById('user_approval_required');

  if (titleInput) titleInput.value = submission.title || '';
  if (authorInput) authorInput.value = submission.author_name || '';
  if (amazonInput) amazonInput.value = submission.amazon_url || '';
  if (textualInfoInput) textualInfoInput.value = submission.textual_information || '';
  applyMainCategorySelection(submission.main_category || '');
  applyContentSchemaSelection(submission.content_schema_id || '');
  if (articleStatusInput) articleStatusInput.value = submission.article_status || '';
  if (runImmediatelyInput) runImmediatelyInput.checked = submission.run_immediately !== false;
  if (scheduleInput) scheduleInput.value = toDatetimeLocalValue(submission.schedule_execution);
  if (userApprovalInput) userApprovalInput.checked = !!submission.user_approval_required;

  if (otherLinksContainer) {
    const links = Array.isArray(submission.other_links) ? submission.other_links : [];
    otherLinksContainer.innerHTML = '';
    if (links.length === 0) {
      otherLinksContainer.appendChild(createOtherLinkInput());
    } else {
      links.forEach((link) => otherLinksContainer.appendChild(createOtherLinkInput(link)));
    }
    updateOtherLinksUiState();
  }

  updateScheduleState();
}

function openTaskEditOnSubmitForm(taskId, submission = {}) {
  if (!submitForm || !taskId) return;

  editingTaskId = taskId;
  editingTaskBaseSubmission = { ...submission };
  setSubmitFormMode(true);
  initializeMainCategorySources();
  initializeContentSchemaOptions();
  fillSubmitFormFromSubmission(submission);
  showSection('submit-section');

  if (submitResult) {
    submitResult.className = 'form-result';
    submitResult.textContent = '';
  }
}

function collectSubmitEditPayload(baseSubmission = {}) {
  const payload = collectSubmitPayload();
  const otherLinks = readSubmitOtherLinks();

  return {
    title: payload.title,
    author_name: payload.author_name,
    amazon_url: payload.amazon_url,
    goodreads_url: baseSubmission.goodreads_url || null,
    author_site: baseSubmission.author_site || null,
    other_links: otherLinks,
    textual_information: payload.textual_information || null,
    run_immediately: payload.run_immediately,
    schedule_execution: payload.run_immediately ? null : toIsoDateTime(payload.schedule_execution),
    main_category: payload.main_category || null,
    content_schema_id: payload.content_schema_id || null,
    article_status: payload.article_status || null,
    user_approval_required: payload.user_approval_required,
  };
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
  const mainCategory = mainCategoryInput?.value.trim();
  const contentSchemaId = contentSchemaInput?.value.trim();
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
  if (contentSchemaId) payload.content_schema_id = contentSchemaId;
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
    const isEditing = !!editingTaskId;
    const targetTaskId = editingTaskId;

    submitResult.textContent = isEditing ? 'Saving changes...' : 'Submitting...';
    submitResult.className = 'form-result';

    try {
      if (isEditing) {
        const submissionPayload = collectSubmitEditPayload(editingTaskBaseSubmission || {});
        await executeTaskAction(`/tasks/${targetTaskId}`, 'PATCH', { submission: submissionPayload });

        submitResult.className = 'form-result success';
        submitResult.textContent = 'Task updated successfully.';
      } else {
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
      }

      submitForm.reset();
      updateScheduleState();
      resetSubmitFormLinks();
      initializeMainCategorySources();
      initializeContentSchemaOptions();
      clearSubmitEditMode();

      if (targetTaskId && targetTaskId === currentTaskId) {
        fetchTaskDetails(targetTaskId);
      }

      skip = 0;
      fetchTasks();
      fetchStats();
    } catch (err) {
      submitResult.className = 'form-result error';
      submitResult.textContent = normalizeError(err, isEditing ? 'Failed to update task' : 'Failed to submit task');
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
  if (submitButton) setIconButtonContent(submitButton, 'save', editing ? 'Save credential changes' : 'Save credential');
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
    const url = credForm.querySelector('#cred-url');
    const key = credForm.querySelector('#cred-key');
    const username = credForm.querySelector('#cred-username');
    const activeInput = credForm.querySelector('input[name="active"]');

    if (service) service.value = credential.service || 'openai';
    if (name) name.value = credential.name || '';
    if (url) url.value = credential.url || '';
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
      <div class="text-muted small">Service: ${escapeHtml(credential.service || '-')} | URL: ${escapeHtml(credential.url || '-')}</div>
      <div class="text-muted small">Key: ${escapeHtml(credential.key || '****')}</div>
      <div class="text-muted small">Created: ${formatDate(credential.created_at)} | Last Used: ${lastUsed}</div>
      <span class="task-status ${active ? 'status-success' : 'status-warning'}">${status}</span>
    </div>
    <div class="item-actions">
      <button type="button" class="btn btn-secondary btn-xs btn-icon-only" data-action="edit" aria-label="Edit credential" title="Edit credential">
        ${renderIconActionContent('edit', 'Edit credential')}
      </button>
      <button type="button" class="btn btn-secondary btn-xs btn-icon-only" data-action="toggle" aria-label="${active ? 'Deactivate credential' : 'Activate credential'}" title="${active ? 'Deactivate credential' : 'Activate credential'}">
        ${renderIconActionContent('toggle', active ? 'Deactivate credential' : 'Activate credential')}
      </button>
      <button type="button" class="btn btn-secondary btn-xs btn-icon-only" data-action="delete" aria-label="Delete credential" title="Delete credential">
        ${renderIconActionContent('delete', 'Delete credential')}
      </button>
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
      initializeMainCategorySources();
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
      initializeMainCategorySources();
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
    const url = credForm.querySelector('#cred-url')?.value.trim();
    const key = credForm.querySelector('#cred-key')?.value.trim();
    const usernameEmail = credForm.querySelector('#cred-username')?.value.trim();
    const encrypted = !!credForm.querySelector('input[name="encrypted"]')?.checked;
    const active = !!credForm.querySelector('input[name="active"]')?.checked;

    try {
      if (service === 'wordpress' && !url) {
        throw new Error('Base URL is required for WordPress credentials.');
      }

      let response;
      if (editingCredentialId) {
        const payload = {
          name: name || undefined,
          url: url || undefined,
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
            url: url || undefined,
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
      initializeMainCategorySources();
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
  if (submitButton) setIconButtonContent(submitButton, 'save', editing ? 'Save prompt changes' : 'Save prompt');
}

function getPromptProviderLabel(provider) {
  const normalized = String(provider || '').trim().toLowerCase();
  const found = PROMPT_PROVIDER_OPTIONS.find((item) => item.value === normalized);
  if (found) return found.label;
  return normalized ? normalized.toUpperCase() : 'Unknown';
}

function applyPromptCategoryOptions(categories = []) {
  const normalized = Array.from(
    new Set(
      [PROMPT_DEFAULT_CATEGORY, ...(Array.isArray(categories) ? categories : [])]
        .map((item) => String(item || '').trim())
        .filter((item) => item)
    )
  ).sort((a, b) => a.localeCompare(b, 'pt-BR', { sensitivity: 'base' }));

  cachedPromptCategories = normalized;

  if (promptCategoryInput) {
    const selected = String(promptCategoryInput.value || '').trim();
    promptCategoryInput.innerHTML = normalized
      .map((category) => `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`)
      .join('');
    const fallback = normalized.includes(PROMPT_DEFAULT_CATEGORY) ? PROMPT_DEFAULT_CATEGORY : (normalized[0] || '');
    promptCategoryInput.value = normalized.includes(selected) ? selected : fallback;
  }

  if (promptFilterCategoryInput) {
    const selected = String(promptFilterCategoryInput.value || '').trim();
    promptFilterCategoryInput.innerHTML = `<option value="">All categories</option>${normalized
      .map((category) => `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`)
      .join('')}`;
    promptFilterCategoryInput.value = normalized.includes(selected) ? selected : '';
  }
}

function applyPromptProviderOptions(items = []) {
  const values = new Set(PROMPT_PROVIDER_OPTIONS.map((item) => item.value));
  (Array.isArray(items) ? items : []).forEach((item) => {
    const provider = String(item?.provider || '').trim().toLowerCase();
    if (provider && values.has(provider)) values.add(provider);
  });

  const providerOptions = Array.from(values)
    .sort((a, b) => a.localeCompare(b, 'en', { sensitivity: 'base' }))
    .map((value) => ({ value, label: getPromptProviderLabel(value) }));

  if (promptProviderInput) {
    const selected = String(promptProviderInput.value || '').trim().toLowerCase() || PROMPT_DEFAULT_PROVIDER;
    promptProviderInput.innerHTML = providerOptions
      .map((item) => `<option value="${escapeHtml(item.value)}">${escapeHtml(item.label)}</option>`)
      .join('');
    promptProviderInput.value = values.has(selected) ? selected : PROMPT_DEFAULT_PROVIDER;
  }

  if (promptFilterProviderInput) {
    const selected = String(promptFilterProviderInput.value || '').trim().toLowerCase();
    promptFilterProviderInput.innerHTML = `<option value="">All providers</option>${providerOptions
      .map((item) => `<option value="${escapeHtml(item.value)}">${escapeHtml(item.label)}</option>`)
      .join('')}`;
    promptFilterProviderInput.value = values.has(selected) ? selected : '';
  }
}

async function fetchPromptCategories(force = false) {
  if (!force && cachedPromptCategories.length > 0) return cachedPromptCategories;

  const response = await fetch('/settings/prompt-categories');
  const data = await response.json().catch(() => ([]));
  if (!response.ok) throw new Error(parseApiError(data, 'Failed to load prompt categories'));
  if (!Array.isArray(data)) {
    cachedPromptCategories = [PROMPT_DEFAULT_CATEGORY];
    return cachedPromptCategories;
  }

  cachedPromptCategories = data
    .map((item) => String(item || '').trim())
    .filter((item) => item);
  if (!cachedPromptCategories.includes(PROMPT_DEFAULT_CATEGORY)) {
    cachedPromptCategories.unshift(PROMPT_DEFAULT_CATEGORY);
  }
  return cachedPromptCategories;
}

async function initializePromptCategories(force = false) {
  try {
    const categories = await fetchPromptCategories(force);
    applyPromptCategoryOptions(categories);
  } catch (_) {
    applyPromptCategoryOptions([PROMPT_DEFAULT_CATEGORY]);
  }
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
  if (model) model.value = PROMPT_DEFAULT_MODEL;
  if (temperature) temperature.value = '0.7';
  if (maxTokens) maxTokens.value = '800';
  if (promptCategoryInput) promptCategoryInput.value = PROMPT_DEFAULT_CATEGORY;
  if (promptProviderInput) promptProviderInput.value = PROMPT_DEFAULT_PROVIDER;
  if (promptFormResult) {
    promptFormResult.className = 'form-result';
    promptFormResult.textContent = '';
  }

  setPromptFormMode(false);
}

function getPromptFilters() {
  return {
    category: String(promptFilterCategoryInput?.value || '').trim(),
    provider: String(promptFilterProviderInput?.value || '').trim().toLowerCase(),
    name: String(promptFilterNameInput?.value || '').trim(),
  };
}

function buildPromptFilterParams() {
  const filters = getPromptFilters();
  const params = new URLSearchParams();
  if (filters.category) params.set('category', filters.category);
  if (filters.provider) params.set('provider', filters.provider);
  if (filters.name) params.set('name', filters.name);
  return params.toString();
}

function openPromptModal(prompt = null) {
  resetPromptForm();
  if (prompt && promptForm) {
    editingPromptId = prompt.id;

    promptForm.querySelector('#prompt-name').value = prompt.name || '';
    promptForm.querySelector('#prompt-purpose').value = prompt.purpose || '';
    if (promptCategoryInput) promptCategoryInput.value = prompt.category || PROMPT_DEFAULT_CATEGORY;
    if (promptProviderInput) {
      const providerValue = String(prompt.provider || PROMPT_DEFAULT_PROVIDER).toLowerCase();
      const hasOption = Array.from(promptProviderInput.options).some((option) => option.value === providerValue);
      promptProviderInput.value = hasOption ? providerValue : PROMPT_DEFAULT_PROVIDER;
    }
    promptForm.querySelector('#prompt-short').value = prompt.short_description || '';
    promptForm.querySelector('#prompt-system').value = prompt.system_prompt || '';
    promptForm.querySelector('#prompt-user').value = prompt.user_prompt || '';
    promptForm.querySelector('#prompt-output-format').value = prompt.expected_output_format || prompt.schema_example || '';
    promptForm.querySelector('#prompt-model').value = prompt.model_id || PROMPT_DEFAULT_MODEL;
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
      <div class="text-muted small">Category: ${escapeHtml(prompt.category || PROMPT_DEFAULT_CATEGORY)} | Provider: ${escapeHtml(getPromptProviderLabel(prompt.provider || PROMPT_DEFAULT_PROVIDER))}</div>
      <div class="text-muted small">Purpose: ${escapeHtml(prompt.purpose || '-')} | Model: ${escapeHtml(prompt.model_id || '-')}</div>
      <div class="text-muted small">${escapeHtml(shortSystem)}${(prompt.system_prompt || '').length > 160 ? '...' : ''}</div>
      <span class="task-status ${active ? 'status-success' : 'status-warning'}">${active ? 'Active' : 'Inactive'}</span>
    </div>
    <div class="item-actions">
      <button type="button" class="btn btn-secondary btn-xs btn-icon-only" data-action="edit" aria-label="Edit prompt" title="Edit prompt">
        ${renderIconActionContent('edit', 'Edit prompt')}
      </button>
      <button type="button" class="btn btn-secondary btn-xs btn-icon-only" data-action="toggle" aria-label="${active ? 'Deactivate prompt' : 'Activate prompt'}" title="${active ? 'Deactivate prompt' : 'Activate prompt'}">
        ${renderIconActionContent('toggle', active ? 'Deactivate prompt' : 'Activate prompt')}
      </button>
      <button type="button" class="btn btn-secondary btn-xs btn-icon-only" data-action="delete" aria-label="Delete prompt" title="Delete prompt">
        ${renderIconActionContent('delete', 'Delete prompt')}
      </button>
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
    const query = buildPromptFilterParams();
    const response = await fetch(`/settings/prompts${query ? `?${query}` : ''}`);
    const items = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(items, 'Failed to load prompts'));

    applyPromptProviderOptions(Array.isArray(items) ? items : []);

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
      category: promptForm.querySelector('#prompt-category')?.value.trim() || PROMPT_DEFAULT_CATEGORY,
      provider: promptForm.querySelector('#prompt-provider')?.value.trim().toLowerCase() || PROMPT_DEFAULT_PROVIDER,
      short_description: promptForm.querySelector('#prompt-short')?.value.trim() || undefined,
      system_prompt: promptForm.querySelector('#prompt-system')?.value,
      user_prompt: promptForm.querySelector('#prompt-user')?.value,
      expected_output_format: promptForm.querySelector('#prompt-output-format')?.value.trim() || undefined,
      model_id: promptForm.querySelector('#prompt-model')?.value.trim() || PROMPT_DEFAULT_MODEL,
      temperature: parseFloat(promptForm.querySelector('#prompt-temp')?.value || '0.7'),
      max_tokens: parseInt(promptForm.querySelector('#prompt-tokens')?.value || '800', 10),
      active: !!promptForm.querySelector('input[name="active"]')?.checked,
    };

    try {
      if (!payload.name || !payload.purpose || !payload.category || !payload.provider || !payload.system_prompt || !payload.user_prompt) {
        throw new Error('Prompt name, purpose, category, provider, system prompt, and user prompt are required.');
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

function parseOptionalNonNegativeInteger(value, fieldLabel) {
  if (value === '' || value === null || value === undefined) return null;
  const parsed = Number.parseInt(String(value), 10);
  if (Number.isNaN(parsed) || parsed < 0) {
    throw new Error(`${fieldLabel} must be a non-negative integer.`);
  }
  return parsed;
}

function parseRequiredNonNegativeInteger(value, fieldLabel) {
  const parsed = Number.parseInt(String(value ?? ''), 10);
  if (Number.isNaN(parsed) || parsed < 0) {
    throw new Error(`${fieldLabel} must be a non-negative integer.`);
  }
  return parsed;
}

function parseCommaSeparatedValues(value) {
  return String(value || '')
    .split(',')
    .map((item) => item.trim())
    .filter((item) => item);
}

async function fetchPromptOptions(force = false) {
  if (!force && cachedPromptOptions.length > 0) return cachedPromptOptions;

  const response = await fetch('/settings/prompts');
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(parseApiError(data, 'Failed to load prompt options'));
  if (!Array.isArray(data)) {
    cachedPromptOptions = [];
    return cachedPromptOptions;
  }

  cachedPromptOptions = data.map((item) => ({
    id: String(item.id || ''),
    name: String(item.name || ''),
    purpose: String(item.purpose || ''),
    category: String(item.category || PROMPT_DEFAULT_CATEGORY),
    provider: String(item.provider || PROMPT_DEFAULT_PROVIDER).toLowerCase(),
    active: item.active !== false,
  }));
  return cachedPromptOptions;
}

function buildTocPromptOptions(selectedPromptId = '') {
  const selectedId = String(selectedPromptId || '');
  const options = cachedPromptOptions
    .map((item) => {
      const selected = selectedId && item.id === selectedId ? 'selected' : '';
      const label = `${item.name || '-'}${item.purpose ? ` (${item.purpose})` : ''}${item.active ? '' : ' [inactive]'}`;
      return `<option value="${escapeHtml(item.id)}" ${selected}>${escapeHtml(label)}</option>`;
    })
    .join('');

  return `<option value="">No prompt</option>${options}`;
}

function updateTocSpecificHintState(row) {
  if (!row) return;
  const modeSelect = row.querySelector('.toc-content-mode');
  const hintField = row.querySelector('.toc-specific-content-hint');
  if (!(modeSelect instanceof HTMLSelectElement) || !(hintField instanceof HTMLTextAreaElement)) return;

  const isSpecific = modeSelect.value === 'specific';
  hintField.disabled = !isSpecific;
  hintField.placeholder = isSpecific
    ? 'Describe the specific content this section must include.'
    : 'Optional guidance for dynamic generation.';
}

function createTocItemCard(item = {}) {
  const level = String(item.level || 'h2').toLowerCase() === 'h3' ? 'h3' : 'h2';
  const contentMode = String(item.content_mode || 'dynamic').toLowerCase() === 'specific' ? 'specific' : 'dynamic';
  const titleTemplate = String(item.title_template || '');
  const specificContentHint = String(item.specific_content_hint || '');
  const minParagraphs = item.min_paragraphs ?? '';
  const maxParagraphs = item.max_paragraphs ?? '';
  const minWords = item.min_words ?? '';
  const maxWords = item.max_words ?? '';
  const sourceFields = Array.isArray(item.source_fields) ? item.source_fields.join(', ') : '';
  const promptId = item.prompt_id ? String(item.prompt_id) : '';

  const card = document.createElement('article');
  card.className = 'toc-item-card';
  card.innerHTML = `
    <div class="toc-item-header">
      <h5 class="toc-item-index">Item</h5>
      <button type="button" class="btn btn-danger btn-xs btn-icon-only toc-remove-btn" aria-label="Remove TOC item" title="Remove TOC item">
        ${renderIconActionContent('delete', 'Remove TOC item')}
      </button>
    </div>
    <div class="toc-item-grid">
      <div class="form-group">
        <label class="form-label">Level</label>
        <select class="form-input toc-level">
          <option value="h2" ${level === 'h2' ? 'selected' : ''}>H2</option>
          <option value="h3" ${level === 'h3' ? 'selected' : ''}>H3</option>
        </select>
      </div>
      <div class="form-group toc-item-grid-span-2">
        <label class="form-label">Title/Sub-title Template *</label>
        <input type="text" class="form-input toc-title-template" value="${escapeHtml(titleTemplate)}" placeholder="Ex: Bibliographic Data">
      </div>
      <div class="form-group">
        <label class="form-label">Content Type</label>
        <select class="form-input toc-content-mode">
          <option value="dynamic" ${contentMode === 'dynamic' ? 'selected' : ''}>Dynamic</option>
          <option value="specific" ${contentMode === 'specific' ? 'selected' : ''}>Specific Content</option>
        </select>
      </div>
      <div class="form-group toc-item-grid-span-2">
        <label class="form-label">Specific Content Hint</label>
        <textarea class="form-textarea toc-specific-content-hint" rows="2">${escapeHtml(specificContentHint)}</textarea>
      </div>
      <div class="form-group">
        <label class="form-label">Min Paragraphs</label>
        <input type="number" min="0" step="1" class="form-input toc-min-paragraphs" value="${escapeHtml(minParagraphs)}">
      </div>
      <div class="form-group">
        <label class="form-label">Max Paragraphs</label>
        <input type="number" min="0" step="1" class="form-input toc-max-paragraphs" value="${escapeHtml(maxParagraphs)}">
      </div>
      <div class="form-group">
        <label class="form-label">Min Words</label>
        <input type="number" min="0" step="1" class="form-input toc-min-words" value="${escapeHtml(minWords)}">
      </div>
      <div class="form-group">
        <label class="form-label">Max Words</label>
        <input type="number" min="0" step="1" class="form-input toc-max-words" value="${escapeHtml(maxWords)}">
      </div>
      <div class="form-group toc-item-grid-span-2">
        <label class="form-label">Database Fields (comma-separated)</label>
        <input type="text" class="form-input toc-source-fields" value="${escapeHtml(sourceFields)}" placeholder="extracted.title, extracted.authors, summaries.summary_text">
      </div>
      <div class="form-group toc-item-grid-span-2">
        <label class="form-label">Prompt</label>
        <select class="form-input toc-prompt-id">
          ${buildTocPromptOptions(promptId)}
        </select>
      </div>
    </div>
  `;

  const modeSelect = card.querySelector('.toc-content-mode');
  modeSelect?.addEventListener('change', () => updateTocSpecificHintState(card));
  updateTocSpecificHintState(card);

  card.querySelector('.toc-remove-btn')?.addEventListener('click', () => {
    card.remove();
    refreshTocItemLabels();
    if (tocItemsContainer && tocItemsContainer.children.length === 0) {
      addTocItemCard();
    }
  });

  return card;
}

function refreshTocItemLabels() {
  if (!tocItemsContainer) return;
  const rows = Array.from(tocItemsContainer.querySelectorAll('.toc-item-card'));
  rows.forEach((row, index) => {
    const title = row.querySelector('.toc-item-index');
    if (title) title.textContent = `Item ${index + 1}`;
  });
}

function addTocItemCard(item = null) {
  if (!tocItemsContainer) return;
  tocItemsContainer.appendChild(createTocItemCard(item || {}));
  refreshTocItemLabels();
}

function setContentSchemaFormMode(editing) {
  const submitButton = contentSchemaForm?.querySelector('button[type="submit"]');
  if (contentSchemaModalTitle) {
    contentSchemaModalTitle.textContent = editing ? 'Edit Content Schema' : 'Create Content Schema';
  }
  if (submitButton) {
    setIconButtonContent(submitButton, 'save', editing ? 'Save content schema changes' : 'Save content schema');
  }
}

function resetContentSchemaForm() {
  editingContentSchemaId = null;
  if (!contentSchemaForm) return;

  contentSchemaForm.reset();
  const active = contentSchemaForm.querySelector('#content-schema-active');
  const targetType = contentSchemaForm.querySelector('#content-schema-target-type');
  const internalLinksCount = contentSchemaForm.querySelector('#content-schema-internal-links');
  const externalLinksCount = contentSchemaForm.querySelector('#content-schema-external-links');
  if (active instanceof HTMLInputElement) active.checked = true;
  if (targetType instanceof HTMLSelectElement) targetType.value = 'book_review';
  if (internalLinksCount instanceof HTMLInputElement) internalLinksCount.value = '0';
  if (externalLinksCount instanceof HTMLInputElement) externalLinksCount.value = '0';

  if (tocItemsContainer) {
    tocItemsContainer.innerHTML = '';
    addTocItemCard({
      level: 'h2',
      title_template: '',
      content_mode: 'dynamic',
    });
  }

  if (contentSchemaFormResult) {
    contentSchemaFormResult.className = 'form-result';
    contentSchemaFormResult.textContent = '';
  }
  setContentSchemaFormMode(false);
}

async function openContentSchemaModal(schema = null) {
  let promptLoadError = null;
  try {
    await fetchPromptOptions(true);
  } catch (err) {
    cachedPromptOptions = [];
    promptLoadError = normalizeError(err, 'Failed to load prompt options');
  }
  resetContentSchemaForm();

  if (schema && contentSchemaForm) {
    editingContentSchemaId = schema.id;
    contentSchemaForm.querySelector('#content-schema-name').value = schema.name || '';
    contentSchemaForm.querySelector('#content-schema-target-type').value = schema.target_type || 'book_review';
    contentSchemaForm.querySelector('#content-schema-description').value = schema.description || '';
    contentSchemaForm.querySelector('#content-schema-min-total-words').value = schema.min_total_words ?? '';
    contentSchemaForm.querySelector('#content-schema-max-total-words').value = schema.max_total_words ?? '';
    contentSchemaForm.querySelector('#content-schema-internal-links').value = String(schema.internal_links_count ?? 0);
    contentSchemaForm.querySelector('#content-schema-external-links').value = String(schema.external_links_count ?? 0);
    contentSchemaForm.querySelector('#content-schema-active').checked = schema.active !== false;

    if (tocItemsContainer) {
      tocItemsContainer.innerHTML = '';
      const tocItems = Array.isArray(schema.toc_template) ? schema.toc_template : [];
      if (tocItems.length === 0) {
        addTocItemCard();
      } else {
        tocItems.forEach((item) => addTocItemCard(item));
      }
    }
    setContentSchemaFormMode(true);
  }

  if (promptLoadError && contentSchemaFormResult) {
    contentSchemaFormResult.className = 'form-result error';
    contentSchemaFormResult.textContent = `${promptLoadError}. You can still save and assign prompts later.`;
  }

  if (contentSchemaEditorPanel) {
    contentSchemaEditorPanel.classList.add('active');
    contentSchemaEditorPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function closeContentSchemaModal() {
  resetContentSchemaForm();
  if (contentSchemaEditorPanel) {
    contentSchemaEditorPanel.classList.remove('active');
  }
}

function collectTocTemplatePayload() {
  if (!tocItemsContainer) return [];

  const rows = Array.from(tocItemsContainer.querySelectorAll('.toc-item-card'));
  if (rows.length === 0) {
    throw new Error('At least one TOC item is required.');
  }

  return rows.map((row, index) => {
    const level = row.querySelector('.toc-level')?.value === 'h3' ? 'h3' : 'h2';
    const titleTemplate = row.querySelector('.toc-title-template')?.value.trim() || '';
    const contentMode = row.querySelector('.toc-content-mode')?.value === 'specific' ? 'specific' : 'dynamic';
    const specificContentHint = row.querySelector('.toc-specific-content-hint')?.value.trim() || null;
    const minParagraphs = parseOptionalNonNegativeInteger(
      row.querySelector('.toc-min-paragraphs')?.value,
      'TOC min paragraphs'
    );
    const maxParagraphs = parseOptionalNonNegativeInteger(
      row.querySelector('.toc-max-paragraphs')?.value,
      'TOC max paragraphs'
    );
    const minWords = parseOptionalNonNegativeInteger(
      row.querySelector('.toc-min-words')?.value,
      'TOC min words'
    );
    const maxWords = parseOptionalNonNegativeInteger(
      row.querySelector('.toc-max-words')?.value,
      'TOC max words'
    );
    const sourceFields = parseCommaSeparatedValues(row.querySelector('.toc-source-fields')?.value);
    const promptId = row.querySelector('.toc-prompt-id')?.value || null;

    if (!titleTemplate) {
      throw new Error(`TOC item ${index + 1}: title template is required.`);
    }
    if (minParagraphs !== null && maxParagraphs !== null && maxParagraphs < minParagraphs) {
      throw new Error(`TOC item ${index + 1}: max paragraphs must be >= min paragraphs.`);
    }
    if (minWords !== null && maxWords !== null && maxWords < minWords) {
      throw new Error(`TOC item ${index + 1}: max words must be >= min words.`);
    }

    return {
      level,
      title_template: titleTemplate,
      content_mode: contentMode,
      specific_content_hint: specificContentHint,
      min_paragraphs: minParagraphs,
      max_paragraphs: maxParagraphs,
      min_words: minWords,
      max_words: maxWords,
      source_fields: sourceFields,
      prompt_id: promptId,
      position: index,
    };
  });
}

function collectContentSchemaPayload() {
  if (!contentSchemaForm) throw new Error('Content schema form is unavailable.');

  const name = contentSchemaForm.querySelector('#content-schema-name')?.value.trim() || '';
  const targetType = contentSchemaForm.querySelector('#content-schema-target-type')?.value.trim() || 'book_review';
  const description = contentSchemaForm.querySelector('#content-schema-description')?.value.trim() || null;
  const minTotalWords = parseOptionalNonNegativeInteger(
    contentSchemaForm.querySelector('#content-schema-min-total-words')?.value,
    'Min total words'
  );
  const maxTotalWords = parseOptionalNonNegativeInteger(
    contentSchemaForm.querySelector('#content-schema-max-total-words')?.value,
    'Max total words'
  );
  const internalLinksCount = parseRequiredNonNegativeInteger(
    contentSchemaForm.querySelector('#content-schema-internal-links')?.value || '0',
    'Internal links count'
  );
  const externalLinksCount = parseRequiredNonNegativeInteger(
    contentSchemaForm.querySelector('#content-schema-external-links')?.value || '0',
    'External links count'
  );
  const active = !!contentSchemaForm.querySelector('#content-schema-active')?.checked;
  const tocTemplate = collectTocTemplatePayload();

  if (!name) throw new Error('Schema name is required.');
  if (minTotalWords !== null && maxTotalWords !== null && maxTotalWords < minTotalWords) {
    throw new Error('Max total words must be greater than or equal to min total words.');
  }

  return {
    name,
    target_type: targetType,
    description,
    min_total_words: minTotalWords,
    max_total_words: maxTotalWords,
    toc_template: tocTemplate,
    internal_links_count: internalLinksCount,
    external_links_count: externalLinksCount,
    active,
  };
}

function renderContentSchemaItem(schema) {
  const li = document.createElement('li');
  li.className = 'item-card clickable-card';
  li.setAttribute('role', 'button');
  li.setAttribute('tabindex', '0');

  const active = !!schema.active;
  const minWords = schema.min_total_words ?? '-';
  const maxWords = schema.max_total_words ?? '-';
  const tocItemsCount = Array.isArray(schema.toc_template) ? schema.toc_template.length : 0;

  li.innerHTML = `
    <div>
      <strong>${escapeHtml(schema.name || '-')}</strong>
      <div class="text-muted small">${escapeHtml(schema.description || '')}</div>
      <div class="text-muted small">Type: ${escapeHtml(schema.target_type || '-')} | Words: ${escapeHtml(minWords)} - ${escapeHtml(maxWords)}</div>
      <div class="text-muted small">TOC Items: ${escapeHtml(tocItemsCount)} | Internal Links: ${escapeHtml(schema.internal_links_count || 0)} | External Links: ${escapeHtml(schema.external_links_count || 0)}</div>
      <span class="task-status ${active ? 'status-success' : 'status-warning'}">${active ? 'Active' : 'Inactive'}</span>
    </div>
    <div class="item-actions">
      <button type="button" class="btn btn-secondary btn-xs btn-icon-only" data-action="edit" aria-label="Edit content schema" title="Edit content schema">
        ${renderIconActionContent('edit', 'Edit content schema')}
      </button>
      <button type="button" class="btn btn-secondary btn-xs btn-icon-only" data-action="toggle" aria-label="${active ? 'Deactivate content schema' : 'Activate content schema'}" title="${active ? 'Deactivate content schema' : 'Activate content schema'}">
        ${renderIconActionContent('toggle', active ? 'Deactivate content schema' : 'Activate content schema')}
      </button>
      <button type="button" class="btn btn-secondary btn-xs btn-icon-only" data-action="delete" aria-label="Delete content schema" title="Delete content schema">
        ${renderIconActionContent('delete', 'Delete content schema')}
      </button>
    </div>
  `;

  const openEditor = () => openContentSchemaModal(schema).catch((err) => {
    if (contentSchemaResult) {
      contentSchemaResult.className = 'form-result error';
      contentSchemaResult.textContent = normalizeError(err, 'Failed to open content schema');
    }
  });

  li.querySelector('[data-action="edit"]')?.addEventListener('click', (event) => {
    event.stopPropagation();
    openEditor();
  });

  li.addEventListener('click', (event) => {
    if (event.target instanceof Element && event.target.closest('button, a, input, select, textarea, label')) return;
    openEditor();
  });

  li.addEventListener('keydown', (event) => {
    if (event.target instanceof Element && event.target.closest('button, a, input, select, textarea, label')) return;
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      openEditor();
    }
  });

  li.querySelector('[data-action="toggle"]')?.addEventListener('click', async (event) => {
    event.stopPropagation();
    try {
      const response = await fetch(`/settings/content-schemas/${schema.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ active: !active }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseApiError(data, 'Failed to update content schema'));

      if (contentSchemaResult) {
        contentSchemaResult.className = 'form-result success';
        contentSchemaResult.textContent = 'Content schema updated successfully.';
      }
      fetchContentSchemas();
    } catch (err) {
      if (contentSchemaResult) {
        contentSchemaResult.className = 'form-result error';
        contentSchemaResult.textContent = normalizeError(err, 'Failed to update content schema');
      }
    }
  });

  li.querySelector('[data-action="delete"]')?.addEventListener('click', async (event) => {
    event.stopPropagation();
    if (!confirm(`Delete content schema "${schema.name || schema.id}"?`)) return;

    try {
      const response = await fetch(`/settings/content-schemas/${schema.id}`, { method: 'DELETE' });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(parseApiError(data, 'Failed to delete content schema'));
      }

      if (editingContentSchemaId === schema.id) {
        resetContentSchemaForm();
      }

      if (contentSchemaResult) {
        contentSchemaResult.className = 'form-result success';
        contentSchemaResult.textContent = 'Content schema deleted successfully.';
      }
      fetchContentSchemas();
    } catch (err) {
      if (contentSchemaResult) {
        contentSchemaResult.className = 'form-result error';
        contentSchemaResult.textContent = normalizeError(err, 'Failed to delete content schema');
      }
    }
  });

  return li;
}

async function fetchContentSchemas() {
  if (!contentSchemaList) return;

  contentSchemaList.innerHTML = '<li class="loading">Loading...</li>';

  try {
    const response = await fetch('/settings/content-schemas');
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(parseApiError(data, 'Failed to load content schemas'));

    contentSchemaList.innerHTML = '';
    if (!Array.isArray(data) || data.length === 0) {
      contentSchemaList.innerHTML = '<li class="empty-state">No content schemas configured</li>';
      return;
    }

    data.forEach((schema) => contentSchemaList.appendChild(renderContentSchemaItem(schema)));
  } catch (err) {
    contentSchemaList.innerHTML = `<li class="empty-state">Error: ${escapeHtml(normalizeError(err, 'Failed to load content schemas'))}</li>`;
  } finally {
    initializePromptCategories(true).catch(() => {});
  }
}

if (contentSchemaForm) {
  contentSchemaForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (contentSchemaFormResult) {
      contentSchemaFormResult.className = 'form-result';
      contentSchemaFormResult.textContent = editingContentSchemaId ? 'Updating...' : 'Saving...';
    }

    try {
      const payload = collectContentSchemaPayload();
      const endpoint = editingContentSchemaId
        ? `/settings/content-schemas/${editingContentSchemaId}`
        : '/settings/content-schemas';
      const method = editingContentSchemaId ? 'PATCH' : 'POST';

      const response = await fetch(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(parseApiError(data, 'Failed to save content schema'));

      if (contentSchemaResult) {
        contentSchemaResult.className = 'form-result success';
        contentSchemaResult.textContent = editingContentSchemaId
          ? 'Content schema updated successfully.'
          : 'Content schema created successfully.';
      }

      closeContentSchemaModal();
      fetchContentSchemas();
    } catch (err) {
      if (contentSchemaFormResult) {
        contentSchemaFormResult.className = 'form-result error';
        contentSchemaFormResult.textContent = normalizeError(err, 'Failed to save content schema');
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
          <button type="button" class="btn btn-primary btn-icon-only" aria-label="Configure pipeline" title="Configure pipeline">
            ${renderIconActionContent('configure', 'Configure pipeline')}
          </button>
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
      const delaySeconds = Math.max(0, Number.parseInt(step?.delay_seconds ?? 0, 10) || 0);
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
        <article class="pipeline-step-card is-collapsed">
          <div class="pipeline-step-header">
            <h4>${escapeHtml(step.name || step.id || '-')}</h4>
            <div class="pipeline-step-header-actions">
              <span class="task-status ${step.uses_ai ? 'status-info' : 'status-warning'}">${step.uses_ai ? 'AI' : 'System'}</span>
              <button
                type="button"
                class="pipeline-step-toggle-btn"
                data-step-id="${escapeHtml(step.id)}"
                aria-expanded="false"
                aria-label="Expand step"
                title="Expand step"
              >
                <svg class="icon-expand" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M14 10L21 3M16 3h5v5M10 14L3 21M3 16v5h5"></path>
                </svg>
                <svg class="icon-collapse" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                  <path d="M21 3l-7 7M16 10h5V5M3 21l7-7M8 14H3v5"></path>
                </svg>
              </button>
            </div>
          </div>
          <div class="pipeline-step-body">
            <p class="text-muted">${escapeHtml(step.description || '')}</p>
            <div class="pipeline-step-meta">
              <span><strong>ID:</strong> ${escapeHtml(step.id || '-')}</span>
              <span><strong>Usage Type:</strong> ${escapeHtml(step.type || '-')}</span>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">Step Delay (seconds)</label>
                <input
                  type="number"
                  min="0"
                  step="1"
                  class="form-input pipeline-delay-input"
                  data-step-id="${escapeHtml(step.id)}"
                  value="${delaySeconds}"
                >
              </div>
            </div>
            ${step.uses_ai
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
              </div>
            `
              : ''}
            <div class="task-actions">
              <button
                type="button"
                class="btn btn-primary btn-icon-only pipeline-step-save-btn"
                data-step-id="${escapeHtml(step.id)}"
                aria-label="Save step configuration"
                title="Save step configuration"
              >
                ${renderIconActionContent('save', 'Save step configuration')}
              </button>
            </div>
          </div>
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

function wirePipelineStepToggles() {
  const toggleButtons = document.querySelectorAll('.pipeline-step-toggle-btn');
  toggleButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const card = button.closest('.pipeline-step-card');
      if (!card) return;

      card.classList.toggle('is-collapsed');
      const collapsed = card.classList.contains('is-collapsed');
      button.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
      button.setAttribute('aria-label', collapsed ? 'Expand step' : 'Collapse step');
      button.setAttribute('title', collapsed ? 'Expand step' : 'Collapse step');
    });
  });
}

function wirePipelineDetailsActions(pipelineId) {
  wirePipelineStepToggles();

  const saveButtons = document.querySelectorAll('.pipeline-step-save-btn');
  saveButtons.forEach((button) => {
    button.addEventListener('click', async () => {
      const stepId = button.dataset.stepId;
      if (!stepId) return;

      const row = button.closest('.pipeline-step-card');
      const credentialSelect = row?.querySelector('.pipeline-credential-select');
      const promptSelect = row?.querySelector('.pipeline-prompt-select');
      const delayInput = row?.querySelector('.pipeline-delay-input');

      const delayRaw = delayInput?.value ?? '0';
      const delaySeconds = Number.parseInt(delayRaw, 10);
      if (Number.isNaN(delaySeconds) || delaySeconds < 0) {
        setPipelinesResult('Step delay must be an integer >= 0.', true);
        return;
      }

      const payload = {
        delay_seconds: delaySeconds,
      };
      if (credentialSelect) {
        payload.credential_id = credentialSelect.value ? String(credentialSelect.value) : null;
      }
      if (promptSelect) {
        payload.prompt_id = promptSelect.value ? String(promptSelect.value) : null;
      }

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
    if (!response.ok) throw new Error(parseApiError(data, 'Failed to load pipeline details'));

    currentPipelineDetails = data;
    renderPipelineDetails(data);
    wirePipelineDetailsActions(pipelineId);
  } catch (err) {
    pipelineDetailsContent.innerHTML = `<div class="form-result error">Error: ${escapeHtml(normalizeError(err, 'Failed to load pipeline details'))}</div>`;
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

if (promptFilterCategoryInput) {
  promptFilterCategoryInput.addEventListener('change', () => {
    fetchPrompts();
  });
}

if (promptFilterProviderInput) {
  promptFilterProviderInput.addEventListener('change', () => {
    fetchPrompts();
  });
}

if (promptFilterNameInput) {
  promptFilterNameInput.addEventListener('input', () => {
    window.clearTimeout(promptSearchDebounceTimer);
    promptSearchDebounceTimer = window.setTimeout(() => {
      fetchPrompts();
    }, 300);
  });
}

if (createContentSchemaBtn) {
  createContentSchemaBtn.addEventListener('click', () => {
    openContentSchemaModal().catch((err) => {
      if (contentSchemaResult) {
        contentSchemaResult.className = 'form-result error';
        contentSchemaResult.textContent = normalizeError(err, 'Failed to open content schema');
      }
    });
  });
}

if (contentSchemaCancelBtn) {
  contentSchemaCancelBtn.addEventListener('click', closeContentSchemaModal);
}

if (addTocItemBtn) {
  addTocItemBtn.addEventListener('click', () => addTocItemCard());
}

if (taskEditCancelBtn) {
  taskEditCancelBtn.addEventListener('click', closeTaskEditModal);
}

if (cancelEditTaskBtn) {
  cancelEditTaskBtn.addEventListener('click', () => {
    clearSubmitEditMode();
    if (submitForm) submitForm.reset();
    updateScheduleState();
    resetSubmitFormLinks();
    initializeMainCategorySources();
    initializeContentSchemaOptions();
    if (submitResult) {
      submitResult.className = 'form-result';
      submitResult.textContent = '';
    }
  });
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

if (mainCategoryCredentialInput) {
  mainCategoryCredentialInput.addEventListener('change', async () => {
    const credentialId = String(mainCategoryCredentialInput.value || '');
    storeWordpressCredentialId(credentialId);
    try {
      await fetchMainCategoriesByCredential(credentialId);
    } catch (err) {
      setMainCategoryLoading(normalizeError(err, 'Error loading categories'));
    }
  });
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

  applyStaticActionIcons();
  updateScheduleState();
  initializeMainCategorySources();
  initializeContentSchemaOptions();
  setSubmitFormMode(false);
  updateTaskEditScheduleState();
  resetSubmitFormLinks();

  setCredentialFormMode(false);
  setPromptFormMode(false);
  applyPromptProviderOptions([]);
  initializePromptCategories().catch(() => {});
  setContentSchemaFormMode(false);
  resetContentSchemaForm();
  if (contentSchemaEditorPanel) contentSchemaEditorPanel.classList.remove('active');

  updateHealth();
  fetchStats();
  fetchTasks();
  fetchCredentials();
  fetchContentSchemas();
  fetchPrompts();
  fetchPipelines();
});
