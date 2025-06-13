# MultiAgentAI21

A multi-agent AI system for content creation, data analysis, and customer service using Google's PaLM API.

## Features

- Content Creation Agent: Generate blog posts, social media content, and articles
- Data Analysis Agent: Analyze data and generate insights
- Customer Service Agent: Handle customer queries and support
- Automation Agent: Automate complex processes

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/multiagentai21.git
cd multiagentai21
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with:
```
GOOGLE_API_KEY=your_api_key_here
```

## Usage

### Content Creation
```python
from src.agents import ContentCreatorAgent

agent = ContentCreatorAgent()
response = agent.process("Write a blog post about AI trends")
print(response.content)
```

### Data Analysis
```python
from src.agents import DataAnalysisAgent

agent = DataAnalysisAgent()
response = agent.process("Analyze this dataset...")
print(response.insights)
```

## Development

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
pytest tests/
```

3. Format code:
```bash
black src/ tests/
```

4. Type checking:
```bash
mypy src/
```

## Project Structure

```
multiagentai21/
├── src/               # Source code
│   ├── agents/       # Agent implementations
│   ├── config/       # Configuration
│   ├── utils/        # Utilities
│   └── api/          # API clients
├── tests/            # Test files
└── examples/         # Example usage
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details
