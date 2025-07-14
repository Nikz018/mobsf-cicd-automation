# MobSF CI/CD Automation

Automated mobile security scanning using MobSF (Mobile Security Framework) in CI/CD pipelines.

## Features

- Automated APK/IPA security scanning
- Docker-based MobSF deployment
- GitHub Actions integration
- JSON and PDF report generation

## Quick Start

1. Start MobSF:
   ```bash
   docker compose -f docker/docker-compose.yml up -d
   ```

2. Scan an app:
   ```bash
   python scripts/mobsf_scanner.py --app your-app.apk
   ```

3. View reports in `reports/` directory

## CI/CD Integration

Push code to GitHub to automatically trigger security scans on APK files.