# SeedCamp Monitoring Stack

Complete Prometheus + Grafana monitoring setup for SeedCamp with pre-configured dashboards and alerts.

## Components

- **Prometheus**: Metrics collection and storage
- **Grafana**: Metrics visualization and dashboards
- **AlertManager**: Alert routing and notifications
- **Node Exporter**: System/host metrics
- **cAdvisor**: Container metrics

## Quick Start

### Local Development (Docker Compose)

```bash
cd deploy/monitoring

# Start monitoring stack
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

Access:
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **AlertManager**: http://localhost:9093

### With SeedCamp API

Update `prometheus/prometheus.yml` to point to your SeedCamp API:

```yaml
scrape_configs:
  - job_name: 'seedcamp-api'
    static_configs:
      - targets: ['host.docker.internal:8000']  # macOS/Windows
      # - targets: ['172.17.0.1:8000']          # Linux
```

Then restart Prometheus:
```bash
docker-compose restart prometheus
```

## Metrics Exposed by SeedCamp

The SeedCamp API exposes Prometheus metrics at `GET /metrics`:

### Counters
- `videos_generated_total` - Total videos successfully generated
- `videos_failed_total` - Total videos that failed to generate
- `hero_videos` - Videos generated with Seedance 2.0 (hero tier)
- `catalog_videos` - Videos generated with Seedance 2.0 Fast (catalog tier)

### Gauges
- `script_generation_avg_seconds` - Average script generation time
- `video_generation_avg_seconds` - Average video generation time
- `total_cost_usd` - Cumulative API cost in USD

### Example Output
```
# HELP videos_generated_total Total number of videos generated
# TYPE videos_generated_total counter
videos_generated_total 156.0

# HELP videos_failed_total Total number of failed video generations
# TYPE videos_failed_total counter
videos_failed_total 3.0

# HELP hero_videos Number of hero tier videos generated
# TYPE hero_videos counter
hero_videos 31.0

# HELP catalog_videos Number of catalog tier videos generated
# TYPE catalog_videos counter
catalog_videos 125.0

# HELP script_generation_avg_seconds Average script generation time
# TYPE script_generation_avg_seconds gauge
script_generation_avg_seconds 4.2

# HELP video_generation_avg_seconds Average video generation time
# TYPE video_generation_avg_seconds gauge
video_generation_avg_seconds 28.5

# HELP total_cost_usd Total cost in USD
# TYPE total_cost_usd gauge
total_cost_usd 13.89
```

## Grafana Dashboards

### SeedCamp Overview
Pre-configured dashboard showing:
- Total videos generated (success/failed)
- Total cost (USD)
- Script and video generation times
- Video generation rate over time
- Cost over time
- Hero vs Catalog video distribution
- Success rate gauge

**Import**: Automatically provisioned at `http://localhost:3000/d/seedcamp-overview`

### Creating Custom Dashboards

1. Open Grafana: http://localhost:3000
2. Login: admin/admin
3. Go to Dashboards → New Dashboard
4. Add panel with PromQL queries:

**Example queries**:
```promql
# Videos generated in last hour
increase(videos_generated_total[1h])

# Success rate percentage
videos_generated_total / (videos_generated_total + videos_failed_total) * 100

# Cost per video
total_cost_usd / videos_generated_total

# Hero video ratio
hero_videos / (hero_videos + catalog_videos) * 100
```

## Alerts

Pre-configured alerts in `prometheus/alerts.yml`:

### Critical Alerts
- **APIDown**: API unreachable for >1 minute

### Warning Alerts
- **HighVideoGenerationFailureRate**: >10% failure rate over 5 minutes
- **SlowScriptGeneration**: Script generation >10s
- **SlowVideoGeneration**: Video generation >60s
- **HighCPUUsage**: CPU usage >80% for 5 minutes
- **HighMemoryUsage**: Memory usage >85% for 5 minutes
- **LowDiskSpace**: Disk usage >85% for 10 minutes

### Info Alerts
- **HighDailyCost**: Daily cost >$100
- **HighVideoGenerationVolume**: >100 videos/hour
- **LowHeroVideoRatio**: Hero videos <15% (expected: ~20%)
- **HighHeroVideoRatio**: Hero videos >30% (expected: ~20%)

### Configuring Notifications

Edit `alertmanager/config.yml` to add your notification channels:

#### Slack
```yaml
receivers:
  - name: 'critical'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#seedcamp-alerts'
        title: 'Critical: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

#### Email
```yaml
receivers:
  - name: 'critical'
    email_configs:
      - to: 'ops@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alertmanager@example.com'
        auth_password: 'YOUR_APP_PASSWORD'
```

#### PagerDuty
```yaml
receivers:
  - name: 'critical'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_INTEGRATION_KEY'
```

After editing, restart AlertManager:
```bash
docker-compose restart alertmanager
```

## Production Deployment

### AWS CloudWatch Integration

For ECS deployments, Prometheus can scrape CloudWatch metrics:

1. Install CloudWatch Exporter:
```yaml
# In docker-compose.yml, add:
cloudwatch-exporter:
  image: prom/cloudwatch-exporter:latest
  ports:
    - "9106:9106"
  environment:
    - AWS_ACCESS_KEY_ID=your-key
    - AWS_SECRET_ACCESS_KEY=your-secret
    - AWS_REGION=ap-southeast-1
  volumes:
    - ./cloudwatch-exporter.yml:/config/config.yml
  command:
    - '-config.file=/config/config.yml'
```

2. Add to Prometheus scrape configs:
```yaml
- job_name: 'cloudwatch'
  static_configs:
    - targets: ['cloudwatch-exporter:9106']
```

### GCP Cloud Monitoring Integration

For Cloud Run deployments:

1. Use GCP Managed Prometheus (recommended)
2. Or deploy Prometheus in GKE with GCP exporter

### Kubernetes Deployment

Deploy monitoring stack to Kubernetes:

```bash
# Create namespace
kubectl create namespace monitoring

# Deploy Prometheus
kubectl apply -f deploy/kubernetes/base/prometheus.yaml

# Deploy Grafana
kubectl apply -f deploy/kubernetes/base/grafana.yaml

# Access via port-forward
kubectl port-forward -n monitoring svc/grafana 3000:3000
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```

## Monitoring Best Practices

### 1. Set Retention Policies
```yaml
# In prometheus.yml, add:
storage:
  tsdb:
    retention.time: 15d
    retention.size: 10GB
```

### 2. Add Recording Rules
Create `prometheus/rules.yml`:
```yaml
groups:
  - name: seedcamp_recording_rules
    interval: 30s
    rules:
      # Pre-compute expensive queries
      - record: seedcamp:video_success_rate
        expr: |
          videos_generated_total / 
          (videos_generated_total + videos_failed_total) * 100
      
      - record: seedcamp:cost_per_video
        expr: total_cost_usd / videos_generated_total
```

### 3. Enable Remote Write (Long-term Storage)
```yaml
# In prometheus.yml, add:
remote_write:
  - url: "https://your-prometheus-remote-storage/api/v1/write"
    basic_auth:
      username: "your-username"
      password: "your-password"
```

Options:
- **Grafana Cloud**: Managed Prometheus + Grafana
- **Thanos**: Long-term storage for Prometheus
- **Cortex**: Multi-tenant Prometheus

### 4. Dashboard Snapshots
Export dashboards for backup:
```bash
# Via API
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:3000/api/dashboards/uid/seedcamp-overview > backup.json
```

## Troubleshooting

### Prometheus Not Scraping Metrics

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check if API is reachable from Prometheus container
docker exec seedcamp-prometheus wget -O- http://host.docker.internal:8000/metrics
```

### Grafana Dashboard Not Loading

```bash
# Check Prometheus datasource
curl http://localhost:3000/api/datasources

# Test Prometheus query
curl -G 'http://localhost:9090/api/v1/query' \
  --data-urlencode 'query=videos_generated_total'
```

### AlertManager Not Sending Alerts

```bash
# Check alert status
curl http://localhost:9093/api/v2/alerts

# Check AlertManager logs
docker-compose logs alertmanager

# Test webhook
curl -H "Content-Type: application/json" \
  -d '[{"labels":{"alertname":"TestAlert"}}]' \
  http://localhost:9093/api/v1/alerts
```

### High Memory Usage

```bash
# Check Prometheus memory
docker stats seedcamp-prometheus

# Reduce retention or add limits
prometheus:
  command:
    - '--storage.tsdb.retention.time=7d'
    - '--storage.tsdb.retention.size=5GB'
  deploy:
    resources:
      limits:
        memory: 2G
```

## Cost Optimization

### Free Tier Options
- **Grafana Cloud**: 10k metrics, 50GB logs/month free
- **AWS CloudWatch**: 10 custom metrics free
- **Datadog**: 5 hosts free (not recommended for production)

### Self-Hosted Costs
- **Small deployment**: 1 EC2 t3.small (~$15/month)
- **Medium deployment**: 1 EC2 t3.medium (~$30/month)
- **Storage**: EBS gp3 50GB (~$4/month)

Total: ~$20-35/month for self-hosted monitoring

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [AlertManager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
