# AWS ECS Fargate Deployment with Terraform

This directory contains Terraform configurations for deploying SeedCamp to AWS ECS Fargate with Application Load Balancer.

## Architecture

- **Compute**: ECS Fargate (serverless containers)
- **Load Balancing**: Application Load Balancer (ALB)
- **Networking**: VPC with 2 public subnets across AZs
- **Secrets**: AWS Secrets Manager for API key
- **Logging**: CloudWatch Logs
- **Monitoring**: ECS Container Insights enabled

## Cost Estimate

**Monthly costs** (ap-southeast-1 region):

| Resource | Configuration | Monthly Cost |
|----------|--------------|--------------|
| ECS Fargate (API) | 1 task, 1 vCPU, 2GB RAM | ~$35 |
| ECS Fargate (Dashboard) | 1 task, 0.25 vCPU, 512MB RAM | ~$9 |
| Application Load Balancer | Standard ALB | ~$22 |
| NAT Gateway | Not used (public subnets) | $0 |
| Data Transfer | First 100GB free | ~$0-10 |
| CloudWatch Logs | 7-day retention | ~$2 |
| Secrets Manager | 1 secret | $0.40 |
| **Total** | | **~$68-78/month** |

**Production optimizations**:
- Use Fargate Spot for 70% cost savings on API tasks
- Add auto-scaling based on CPU/memory
- Use S3 for video storage instead of ephemeral /tmp
- Add CloudFront CDN for dashboard

## Prerequisites

1. **AWS CLI configured**:
```bash
aws configure
# Enter your AWS Access Key, Secret Key, and default region
```

2. **Terraform installed** (v1.0+):
```bash
brew install terraform  # macOS
```

3. **Docker images pushed to registry**:
```bash
# Option 1: Docker Hub (public)
docker build -t your-registry/seedcamp-api:latest .
docker build -t your-registry/seedcamp-dashboard:latest -f deploy/docker/Dockerfile.dashboard .
docker push your-registry/seedcamp-api:latest
docker push your-registry/seedcamp-dashboard:latest

# Option 2: AWS ECR (private)
aws ecr create-repository --repository-name seedcamp-api
aws ecr create-repository --repository-name seedcamp-dashboard
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com
docker tag your-registry/seedcamp-api:latest <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/seedcamp-api:latest
docker tag your-registry/seedcamp-dashboard:latest <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/seedcamp-dashboard:latest
docker push <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/seedcamp-api:latest
docker push <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/seedcamp-dashboard:latest
```

## Deployment

### 1. Initialize Terraform

```bash
cd deploy/aws/terraform
terraform init
```

### 2. Create variables file

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
region = "ap-southeast-1"
ark_api_key = "your-actual-api-key"  # REQUIRED

# If using ECR, update image URIs:
api_image = "<account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/seedcamp-api:latest"
dashboard_image = "<account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/seedcamp-dashboard:latest"
```

### 3. Review plan

```bash
terraform plan
```

Expected resources: ~30 resources will be created:
- 1 VPC, 2 subnets, 1 IGW, 1 route table
- 2 security groups, 1 ALB, 2 target groups
- 1 ECS cluster, 2 task definitions, 2 services
- 1 Secrets Manager secret, IAM roles/policies
- 2 CloudWatch log groups

### 4. Apply configuration

```bash
terraform apply
# Type 'yes' when prompted
```

Deployment takes ~5-10 minutes. Output will include:
```
alb_dns_name = "seedcamp-alb-123456789.ap-southeast-1.elb.amazonaws.com"
api_url = "http://seedcamp-alb-123456789.ap-southeast-1.elb.amazonaws.com"
dashboard_url = "http://seedcamp-alb-123456789.ap-southeast-1.elb.amazonaws.com/dashboard"
```

### 5. Verify deployment

```bash
# Check API health
curl http://<alb-dns-name>/health

# View ECS services
aws ecs list-services --cluster seedcamp-cluster --region ap-southeast-1

# View logs
aws logs tail /ecs/seedcamp-api --follow --region ap-southeast-1
```

Access the dashboard at: `http://<alb-dns-name>/dashboard`

## Management

### Update configuration

```bash
# Edit terraform.tfvars (e.g., increase desired_count)
terraform plan
terraform apply
```

### Update Docker images

```bash
# Build and push new images
docker build -t your-registry/seedcamp-api:v2 .
docker push your-registry/seedcamp-api:v2

# Update terraform.tfvars
api_image = "your-registry/seedcamp-api:v2"

# Apply changes (triggers ECS service update)
terraform apply
```

### Scale services

```bash
# Update terraform.tfvars
api_desired_count = 2

terraform apply
```

### View logs

```bash
# API logs
aws logs tail /ecs/seedcamp-api --follow --region ap-southeast-1

# Dashboard logs
aws logs tail /ecs/seedcamp-dashboard --follow --region ap-southeast-1

# Filter for errors
aws logs tail /ecs/seedcamp-api --filter-pattern "ERROR" --region ap-southeast-1
```

### Access ECS task

```bash
# List tasks
aws ecs list-tasks --cluster seedcamp-cluster --region ap-southeast-1

# Execute command in task (requires Session Manager plugin)
aws ecs execute-command \
  --cluster seedcamp-cluster \
  --task <task-id> \
  --container api \
  --interactive \
  --command "/bin/sh"
```

## Cleanup

```bash
terraform destroy
# Type 'yes' when prompted
```

**Warning**: This will delete all resources including logs. To preserve logs, remove the CloudWatch log groups from Terraform state first:
```bash
terraform state rm aws_cloudwatch_log_group.api
terraform state rm aws_cloudwatch_log_group.dashboard
```

## Troubleshooting

### ECS tasks not starting

```bash
# Check service events
aws ecs describe-services \
  --cluster seedcamp-cluster \
  --services seedcamp-api-service \
  --region ap-southeast-1 \
  --query 'services[0].events[0:5]'

# Common issues:
# - Image pull errors: Check ECR permissions or Docker Hub credentials
# - Secrets access: Verify IAM role has secretsmanager:GetSecretValue
# - Health check failures: Check /health endpoint returns 200
```

### ALB health checks failing

```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn <tg-arn> \
  --region ap-southeast-1

# Common issues:
# - Security group: Ensure ALB SG can reach ECS tasks on port 8000/8501
# - Health check path: /health must return 200 for API
# - Container startup: API takes ~10s to start (cold start)
```

### High costs

```bash
# Check ECS service utilization
aws ecs describe-services \
  --cluster seedcamp-cluster \
  --services seedcamp-api-service seedcamp-dashboard-service \
  --region ap-southeast-1

# Optimize:
# 1. Reduce desired_count to 0 when not in use
# 2. Use Fargate Spot (add to task definition)
# 3. Reduce CPU/memory if underutilized
# 4. Delete ALB when not needed (single largest cost)
```

## Production Enhancements

### 1. Add HTTPS with ACM

```hcl
# In main.tf, add:
resource "aws_acm_certificate" "main" {
  domain_name       = "seedcamp.yourdomain.com"
  validation_method = "DNS"
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  certificate_arn   = aws_acm_certificate.main.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}
```

### 2. Add Auto Scaling

```hcl
resource "aws_appautoscaling_target" "api" {
  max_capacity       = 10
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "api_cpu" {
  name               = "api-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
```

### 3. Add S3 for video storage

```hcl
resource "aws_s3_bucket" "videos" {
  bucket = "seedcamp-videos-${data.aws_caller_identity.current.account_id}"
}

# Add IAM policy for ECS tasks to write to S3
# Update OUTPUT_DIR env var to use S3 paths
```

### 4. Add CloudWatch Alarms

```hcl
resource "aws_cloudwatch_metric_alarm" "api_cpu_high" {
  alarm_name          = "seedcamp-api-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 300
  statistic           = "Average"
  threshold           = 80

  dimensions = {
    ClusterName = aws_ecs_cluster.main.name
    ServiceName = aws_ecs_service.api.name
  }
}
```

## Security Considerations

1. **Secrets**: API key stored in Secrets Manager (encrypted at rest)
2. **Network**: Tasks in public subnets (consider private subnets + NAT for production)
3. **IAM**: Least privilege - tasks only have access to their secret
4. **HTTPS**: Add ACM certificate + HTTPS listener for production
5. **WAF**: Consider adding AWS WAF to ALB for DDoS protection

## References

- [AWS ECS Fargate pricing](https://aws.amazon.com/fargate/pricing/)
- [AWS Secrets Manager pricing](https://aws.amazon.com/secrets-manager/pricing/)
- [Terraform AWS Provider docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
