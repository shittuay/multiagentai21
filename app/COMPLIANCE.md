# API Compliance and Safety Guide

This document outlines the comprehensive compliance measures implemented in MultiAgentAI21 to ensure adherence to Google Cloud API Terms of Service and best practices.

## 🛡️ Overview

MultiAgentAI21 includes robust compliance features to prevent API policy violations and ensure responsible AI usage:

- **Rate Limiting**: Conservative API usage limits
- **Content Validation**: Automated content filtering
- **Usage Monitoring**: Comprehensive audit logging
- **Quota Management**: Intelligent quota tracking
- **Fallback Systems**: Graceful degradation when limits are reached

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Conservative API Limits (recommended starting values)
API_REQUESTS_PER_MINUTE=5
API_REQUESTS_PER_HOUR=50  
API_REQUESTS_PER_DAY=200
API_MIN_INTERVAL=12.0

# Enable all compliance features
ENABLE_RATE_LIMITING=true
ENABLE_CONTENT_FILTERING=true
ENABLE_QUOTA_MONITORING=true
ENABLE_USAGE_LOGGING=true
```

### Rate Limiting Levels

**Development (Default):**
- 2 requests/minute
- 30 second minimum interval
- Very conservative limits

**Production:**
- 20 requests/minute
- 3 second minimum interval  
- Higher limits (requires quota increase)

## 🚦 Rate Limiting

### How It Works

1. **Pre-request Validation**: Checks rate limits before making API calls
2. **Intelligent Waiting**: Automatically waits when limits are reached
3. **Quota Tracking**: Monitors daily/hourly/minute usage
4. **Graceful Fallback**: Uses offline responses when quota exceeded

### Usage Example

```python
from src.utils.api_compliance import get_rate_limiter

limiter = get_rate_limiter()

# Check if request can be made
can_proceed, reason = limiter.can_make_request("Your content here")

if can_proceed:
    # Make API request
    response = make_api_call()
    limiter.record_request(success=True)
else:
    print(f"Request blocked: {reason}")
```

## 🔍 Content Validation

### Prohibited Content Detection

Automatically detects and blocks:

- **Personal Information**: SSNs, credit cards, emails
- **Potentially Harmful Content**: Malicious terms, violent content
- **Policy Violations**: Hate speech indicators
- **Spam Patterns**: Common spam phrases

### Custom Validation

```python
from src.utils.api_compliance import ComplianceValidator

is_compliant, violations = ComplianceValidator.validate_content(content)

if not is_compliant:
    print(f"Content blocked: {violations}")
```

## 📊 Usage Monitoring

### Audit Logging

All API interactions are logged to `logs/compliance/` with:

- Request timestamps and content length
- Success/failure status  
- Quota exceeded events
- Content violations
- Rate limit hits

### Compliance Reports

Generate detailed compliance reports:

```python
from src.utils.compliance_monitor import get_compliance_monitor

monitor = get_compliance_monitor()
report = monitor.generate_compliance_report(days=7)

print(f"Success rate: {report['summary']['success_rate']:.1%}")
print(f"Violations: {report['summary']['content_violations']}")
```

## 🎯 Best Practices

### API Usage

1. **Conservative Limits**: Start with very low rate limits
2. **Gradual Increase**: Only increase limits after monitoring usage
3. **Monitor Quota**: Regularly check quota usage in Google Cloud Console
4. **Handle Failures**: Implement proper error handling for quota exceeded

### Content Guidelines  

1. **Business Use**: Focus on legitimate business/educational purposes
2. **No Personal Data**: Avoid processing personal information
3. **Content Review**: Review AI outputs before using
4. **User Consent**: Ensure user consent for data processing

### Monitoring

1. **Regular Reviews**: Check compliance reports weekly
2. **Alert Setup**: Monitor for policy violations
3. **Quota Tracking**: Keep usage well below limits
4. **Documentation**: Maintain audit logs for compliance

## 🚨 Incident Response

### If API Quota is Exceeded

1. **Immediate**: Stop all API requests
2. **Review**: Check compliance logs for cause
3. **Adjust**: Lower rate limits if needed
4. **Monitor**: Wait for quota reset
5. **Resume**: Gradually resume operations

### If Content Violations Detected

1. **Block Request**: Automatically blocked by system
2. **Review Content**: Check what triggered violation
3. **Adjust Filters**: Update content validation if needed
4. **Document**: Log incident for audit

### If Account is Suspended

1. **Stop Operations**: Immediately cease all API activity  
2. **Review Logs**: Examine compliance logs for violations
3. **Submit Appeal**: Use provided appeal process
4. **Implement Fixes**: Address identified issues
5. **Monitor**: Enhanced monitoring after reinstatement

## 🔧 Testing Compliance

Run the compliance test suite:

```bash
python test_compliance.py
```

This tests:
- Rate limiting functionality
- Content validation
- Monitoring systems
- Configuration loading

## 📁 File Structure

```
src/
├── utils/
│   ├── api_compliance.py      # Rate limiting and validation
│   └── compliance_monitor.py  # Audit logging and reporting
├── config/
│   └── compliance_config.py   # Configuration management
└── base_agent.py             # Integrated compliance checks

logs/
└── compliance/               # Audit logs (auto-created)
    ├── compliance_2024-01-01.jsonl
    └── compliance_2024-01-02.jsonl
```

## 📋 Compliance Checklist

Before deployment, ensure:

- [ ] Rate limits configured conservatively
- [ ] Content filtering enabled
- [ ] Audit logging operational
- [ ] Environment variables set
- [ ] Compliance tests passing
- [ ] Error handling implemented
- [ ] Monitoring alerts configured
- [ ] Documentation reviewed
- [ ] Team trained on policies
- [ ] Incident response plan ready

## 🔄 Regular Maintenance

### Weekly Tasks
- Review compliance reports
- Check quota usage in Google Cloud
- Monitor error rates
- Update rate limits if needed

### Monthly Tasks
- Export audit logs for compliance
- Review and update content filters  
- Analyze usage patterns
- Update compliance documentation

## 📞 Support

For compliance-related questions:

1. **Review Documentation**: Check this guide first
2. **Check Logs**: Examine `logs/compliance/` for details
3. **Run Tests**: Use `test_compliance.py` to diagnose issues
4. **Google Cloud Support**: For quota/policy questions
5. **Internal Review**: Document and escalate violations

## ⚖️ Legal Considerations

- All API usage is logged for audit purposes
- Content validation helps ensure policy compliance
- Rate limiting prevents accidental quota violations
- Users are responsible for content they submit
- Regular compliance reviews are recommended

---

**Remember**: These measures are designed to prevent API policy violations and ensure responsible AI usage. When in doubt, err on the side of caution with more conservative limits.