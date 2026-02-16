# Changelog

All notable changes to AdCamp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
