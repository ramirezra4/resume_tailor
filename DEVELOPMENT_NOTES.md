# Resume Tailor Development Notes

## Token Usage Tracking Implementation (2025-03-10)

This document captures the development process and technical decisions made while implementing token usage tracking in Resume Tailor.

### Overview

We added comprehensive token usage tracking to give users visibility into their Claude API usage and associated costs, both for single resume customizations and long-term usage patterns.

### Implementation Details

#### 1. Token Tracking in ResumeTailor Class

```python
# Added to ResumeTailor.__init__
self.token_usage = {
    'analysis_prompt_tokens': 0,
    'analysis_completion_tokens': 0,
    'customization_prompt_tokens': 0,
    'customization_completion_tokens': 0,
    'total_prompt_tokens': 0,
    'total_completion_tokens': 0
}
self.token_log_file = os.path.join(self.log_dir, "token_usage.csv")
```

We added counters for different operation types, enabling granular tracking of token usage across different parts of the resume customization process. This split between analysis and customization provides insights into which operation consumes more resources.

#### 2. CSV Logging System

We implemented a CSV-based logging system to keep a detailed record of all API interactions:

```python
def _log_token_usage(self, operation_type, job_identifier, prompt_tokens, completion_tokens):
    """Log token usage to a CSV file."""
    file_exists = os.path.isfile(self.token_log_file)
    
    with open(self.token_log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'operation', 'job', 'prompt_tokens', 
                            'completion_tokens', 'total_tokens', 'cost_estimate_usd'])
        
        # Calculate approximate cost (prices as of March 2025)
        # Claude 3.7 Sonnet: $15/million tokens input, $75/million tokens output
        input_cost = (prompt_tokens / 1000000) * 15
        output_cost = (completion_tokens / 1000000) * 75
        total_cost = input_cost + output_cost
        
        timestamp = datetime.datetime.now().isoformat()
        total_tokens = prompt_tokens + completion_tokens
        
        writer.writerow([
            timestamp,
            operation_type,
            job_identifier,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            f"{total_cost:.6f}"
        ])
```

This approach enables future data analysis on token usage patterns and cost estimation. We chose CSV for compatibility with spreadsheets and analytics tools.

#### 3. Usage Statistics API

We added a method to generate summary statistics and cost estimates:

```python
def get_token_usage_stats(self):
    """Return token usage statistics and estimated costs."""
    # Calculate costs
    input_cost = (self.token_usage['total_prompt_tokens'] / 1000000) * 15
    output_cost = (self.token_usage['total_completion_tokens'] / 1000000) * 75
    total_cost = input_cost + output_cost
    
    stats = self.token_usage.copy()
    stats.update({
        'total_tokens': stats['total_prompt_tokens'] + stats['total_completion_tokens'],
        'cost_estimate_usd': total_cost
    })
    
    return stats
```

This provides an easy way to access usage data programmatically, both for display and for integrating with other systems.

#### 4. Web Interface Integration

For the web application, we added token tracking to both the analysis and customization steps:

1. API call logging:
```python
# Log token usage in web customization
input_tokens = response.usage.input_tokens
output_tokens = response.usage.output_tokens

tailor.token_usage['customization_prompt_tokens'] += input_tokens
tailor.token_usage['customization_completion_tokens'] += output_tokens
tailor.token_usage['total_prompt_tokens'] += input_tokens
tailor.token_usage['total_completion_tokens'] += output_tokens
```

2. Application storage:
```python
# Store token usage with application
job_entry = {
    # ...existing fields...
    "token_usage": {
        "analysis_tokens": analysis_tokens,
        "customization_tokens": input_tokens + output_tokens,
        "total_tokens": analysis_tokens + input_tokens + output_tokens,
        "cost_estimate_usd": token_stats["cost_estimate_usd"]
    }
}
```

3. HTML display in result.html:
```html
{% if application.token_usage %}
<div class="row mb-3">
    <div class="col-md-4 fw-bold">Token Usage:</div>
    <div class="col-md-8">
        <table class="table table-sm table-borderless">
            <tr>
                <td>Analysis:</td>
                <td>{{ application.token_usage.analysis_tokens|default(0) }} tokens</td>
            </tr>
            <!-- Additional rows -->
        </table>
    </div>
</div>
{% endif %}
```

### Future Analytics Considerations

Currently, applications are stored in a flat JSON file (`applications.json`). For future analytics capabilities, we should consider:

1. **Database Migration**
   - Move from JSON to a proper database (SQLite or PostgreSQL)
   - Create schema with appropriate relationships
   - Implement ORM for data access

2. **Enhanced Data Collection**
   - Track application outcomes (interviews, offers, rejections)
   - Store content changes with before/after comparisons
   - Track which AI suggestions were approved vs. rejected

3. **Analytics Preparation**
   - Add API endpoints for retrieving statistics
   - Implement export functionality for analysis in external tools
   - Consider integration with data visualization libraries

### Cost Calculation Methodology

We based our cost calculations on Claude 3.7 Sonnet pricing as of March 2025:
- Input: $15 per million tokens
- Output: $75 per million tokens

Formula used:
```
input_cost = (prompt_tokens / 1000000) * 15
output_cost = (completion_tokens / 1000000) * 75
total_cost = input_cost + output_cost
```

This pricing should be adjusted if Anthropic changes their rates.

### Conclusion

The token tracking implementation provides users with valuable insights into their API usage and costs. Future improvements could include more sophisticated analytics and visualization of usage patterns over time.

By capturing this implementation detail, we ensure that future developers can understand the design decisions and extend the functionality as needed.