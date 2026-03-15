# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in SeedCamp, please report it privately:

**Email**: suboss87@users.noreply.github.com

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

**Do NOT** open a public GitHub issue for security vulnerabilities.

## Response Timeline

- We will acknowledge your report within 48 hours
- We will provide a detailed response within 7 days
- We will work on a fix and keep you updated on progress

## Supported Versions

| Version | Supported |
|---------|-----------|
| main    | ✅        |
| < 1.0   | ❌        |

## Security Best Practices

### API Keys
- Never commit API keys to version control
- Use environment variables or secret management services
- Rotate keys regularly
- Use separate keys for development, staging, and production

### Deployment
- Use HTTPS only in production
- Enable authentication for production deployments
- Implement rate limiting
- Monitor for unusual activity
- Keep dependencies updated

### Cloud Deployments
- **GCP**: Use Secret Manager for API keys
- **AWS**: Use Secrets Manager or Parameter Store
- **Kubernetes**: Use K8s Secrets with encryption at rest
- **BytePlus**: Follow BytePlus security guidelines

## Known Security Considerations

1. **API Key Exposure**: The ModelArk API key provides access to paid services. Protect it carefully.

2. **Rate Limiting**: Default rate limit is 5 concurrent requests. Adjust based on your subscription.

3. **Video Storage**: Generated videos are stored temporarily. Implement cleanup policies for production.

4. **Input Validation**: The API validates inputs, but always sanitize user-provided data.

## Security Updates

Security patches will be released as soon as possible. Follow releases to stay updated.

## Third-Party Dependencies

We use automated dependency scanning. Regular updates include security patches for:
- FastAPI and dependencies
- Streamlit and dependencies
- Python runtime

Run `pip-audit` to check for known vulnerabilities:
```bash
pip install pip-audit
pip-audit
```
