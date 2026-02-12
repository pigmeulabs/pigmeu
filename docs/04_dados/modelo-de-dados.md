# Modelo de Dados

Banco: MongoDB

## Coleções principais

## `submissions`
Campos principais:
- `_id`
- `title`
- `author_name`
- `amazon_url`
- `goodreads_url`
- `author_site`
- `other_links[]`
- `textual_information`
- `run_immediately`
- `schedule_execution`
- `main_category`
- `article_status`
- `user_approval_required`
- `status`
- `current_step`
- `attempts` (objeto)
- `errors[]`
- `created_at`
- `updated_at`

## `books`
- `_id`
- `submission_id` (ObjectId -> submissions)
- `extracted` (objeto flexível com metadados do livro)
- `last_updated`

## `summaries`
- `_id`
- `book_id` (ObjectId -> books)
- `source_url`
- `source_domain`
- `summary_text`
- `topics[]`
- `key_points[]`
- `credibility`
- `created_at`

## `knowledge_base`
- `_id`
- `book_id` (opcional)
- `submission_id` (opcional)
- `markdown_content`
- `topics_index[]`
- `created_at`
- `updated_at`

## `articles`
- `_id`
- `book_id` (ObjectId -> books)
- `submission_id` (ObjectId -> submissions, opcional)
- `title`
- `content`
- `word_count`
- `status` (`draft`, `in_review`, `approved`, `published`, `archived`)
- `validation_report` (objeto)
- `topics_used[]`
- `wordpress_post_id`
- `wordpress_url`
- `wordpress_categories[]`
- `wordpress_tags[]`
- `meta_description`
- `published_at`
- `created_at`
- `updated_at`

## `articles_drafts`
- `_id`
- `article_id` (ObjectId -> articles)
- `content`
- `created_at`
- `updated_at`

## `credentials`
- `_id`
- `service`
- `name`
- `key`
- `encrypted`
- `username_email`
- `active`
- `created_at`
- `updated_at`
- `last_used_at`

## `prompts`
- `_id`
- `name`
- `purpose`
- `short_description`
- `system_prompt`
- `user_prompt`
- `model_id`
- `temperature`
- `max_tokens`
- `schema_example`
- `active`
- `version`
- `created_at`
- `updated_at`

## Relacionamentos

- `submissions (1) -> (1) books`
- `books (1) -> (N) summaries`
- `books (1) -> (1) knowledge_base`
- `books (1) -> (N) articles`
- `articles (1) -> (1) articles_drafts`
