# Changelog

All notable changes to SeedCamp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-17

### Upgraded
- **Seedance 2.0 support** — new model IDs: `dreamina-seedance-2-0-260128` (Standard) and `dreamina-seedance-2-0-fast-260128` (Fast)
- Updated pricing to April 2026 ModelArk rates (Standard $4.30–7.70/M tok, Fast $3.30–5.60/M tok)
- Native audio generation config (`video_audio_enabled`), offline batch mode (`video_offline`)
- Seedance 2.0 ranked **#2 on Artificial Analysis** (T2V and I2V, April 2026)

### Added
- **Sora migration guide** (`docs/MIGRATE_FROM_SORA.md`) — code diffs, pricing comparison, timeline for Sora shutdown (app Apr 26, API Sep 24)
- "Is SeedCamp for you?" section in README — honest trade-offs, when NOT to use it
- Security Checklist in QUICKSTART — API_KEY, CORS, dashboard auth, rate limit, cost tracker
- Multi-worker startup warning when `WORKERS>1` detected in production
- `pip-audit` security scanning in CI
- CI installs `requirements.txt` alongside `requirements-dev.txt` (fixes slowapi import)
- Deploy workflow set to manual trigger until registry secrets configured

### Changed
- README rewritten for developer ICP — leads with "the plumbing you don't want to rebuild" pitch
- Market research updated with April 2026 data: Sora shutdown, AA rankings, competitive landscape, BytePlus/TikTok USDS de-risking
- Real estate de-prioritized (virtual tours serve that market better)
- Cost tracker documented multi-worker limitation in source with specific mitigation paths

---

## [Unreleased]

### Added
- **AWS Terraform**: Complete ECS Fargate deployment with VPC, ALB, and Secrets Manager
  - `deploy/aws/terraform/main.tf` - Full infrastructure definition (~30 resources)
  - `deploy/aws/terraform/variables.tf` - Configurable parameters
  - `deploy/aws/terraform/outputs.tf` - Service URLs and resource IDs
  - Comprehensive README with cost estimates (~$68-78/month)
  - Support for both Docker Hub and AWS ECR images
- **Prometheus + Grafana Monitoring Stack**: Complete observability solution
  - Pre-configured Prometheus scrape configs for SeedCamp metrics
  - Custom Grafana dashboard ("SeedCamp Overview") with 12 panels
  - AlertManager with critical/warning/info alert rules
  - Node Exporter for system metrics
  - cAdvisor for container metrics
  - Docker Compose setup in `deploy/monitoring/`
  - Alert rules for API health, performance, cost, and SKU ratio monitoring
  - Grafana datasource auto-provisioning
  - Example Slack/Email/PagerDuty notification configs
- Makefile commands: `make monitoring-up` and `make monitoring-down`
- Enterprise repository structure with platform-specific deployment guides
- Deployment configs for GCP Cloud Run, AWS ECS, BytePlus VKE, Railway, Render, Docker Compose
- Terraform templates for infrastructure as code (GCP, AWS, BytePlus)
- Makefile for common development and deployment tasks
- Example Python scripts for basic usage and batch generation
- Comprehensive platform comparison matrix
- Test structure (unit, integration, fixtures)
- CONTRIBUTING.md and SECURITY.md

### Changed
- Reorganized repository structure following Google/Kubernetes standards
- Moved deployment configs to `deploy/` directory by platform
- Moved documentation to `docs/` with architecture subdirectories
- Moved large assets (PDFs, PNGs) to `docs/assets/images/`

## [0.1.0] - 2026-02-16

### Added
- FastAPI backend with video generation endpoints
- Streamlit dashboard for campaign management
- BytePlus ModelArk integration (Seed 1.8, Seedance models)
- Smart model routing (hero vs catalog SKUs)
- Cost tracking and monitoring
- Prometheus metrics endpoint
- Retry logic with exponential backoff
- Docker support
- Kubernetes manifests
- GitHub Actions CI/CD workflow
- Comprehensive documentation

### Features
- AI-powered script generation using Seed 1.8
- Video generation using Seedance 1.0 Pro Fast and 1.5 Pro
- Multi-platform video output (TikTok 9:16, Instagram 1:1, YouTube 16:9)
- Cost optimization with smart routing
- Health check and metrics endpoints
- Environment-based configuration

### Documentation
- README with architecture diagrams
- Deployment guides
- API documentation (Swagger/ReDoc)
- Architecture documentation (logical and physical)

### Infrastructure
- Docker Compose for local development
- Kubernetes manifests for cloud deployment
- Environment configuration examples
- MIT License

## [Pre-release]

### Initial Development
- Project setup and structure
- BytePlus ModelArk API integration
- Basic video generation pipeline
- Cost calculation framework
