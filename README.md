# 📚 Pigmeu Copilot

**Automated technical book review generation and SEO-optimized article publishing for WordPress.**

Transform book information from Amazon, Goodreads, and author sites into complete, SEO-optimized articles ready for publication.

## Features

✨ **Automated Data Extraction**
- Scrape book metadata from Amazon, Goodreads, author sites
- Extract: ISBN, pricing, ratings, publication dates, language, edition info

🤖 **AI-Powered Content Generation**
- Use AI agents to summarize book information from multiple sources
- Generate context and knowledge base from summaries
- Create complete, structured review articles (800-1,333 words)

📝 **Structured Article Generation**
- Automatic H2 sections (3 thematic + 5 fixed sections)
- Optional H3 subsections with minimum word counts
- SEO-optimized titles (≤60 characters)
- Proper paragraph structure (3-6 sentences per paragraph)

🔌 **WordPress Integration**
- Publish articles directly to WordPress via API
- Support for custom metadata and featured images
- Category and tag management

⚙️ **Flexible Configuration**
- Manage AI provider credentials (OpenAI, Claude, etc.)
- Create and manage custom prompts
- Configure article generation parameters

## Quick Start

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- MongoDB Atlas account (with credentials)

### Setup

1. **Clone repository**
   ```bash
   git clone https://github.com/pigmeulabs/pigmeu.git
   cd pigmeu
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Run migrations**
   ```bash
   python scripts/migrate.py
   ```

5. **Start services**
   ```bash
   docker-compose -f infra/docker-compose.yml up --build
   ```

6. **Check health**
   ```bash
   curl http://localhost:8000/health
   ```

API available at: **http://localhost:8000/docs**

## Documentation

- [Setup Instructions](docs/SETUP.md)
- [API Documentation](docs/API.md) (coming soon)
- [Architecture Overview](docs/ARCHITECTURE.md) (coming soon)
- [Legal & Compliance](docs/LEGAL.md) (coming soon)

## Project Structure

```
pigmeu/
├── src/               # Application source code
├── infra/             # Docker & infrastructure
├── scripts/           # Utility scripts
├── docs/              # Documentation
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

## Database

- **Platform**: MongoDB Atlas
- **Collections**: submissions, books, summaries, knowledge_base, articles, credentials, prompts
- **Status**: Configured and ready to use

## License

MIT License - see [LICENSE](LICENSE) for details

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines (coming soon)

---

**Built with ❤️ by Pigmeu Labs**
