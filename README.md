# MultiAgentAI21

An advanced multi-agent AI system for complex problem solving, featuring specialized agents for automation, data analysis, customer service, and content creation.

## Features

- 🤖 **Multiple AI Agents**
  - Automation Agent: Streamline workflows and automate tasks
  - Data Analysis Agent: Extract insights and create visualizations
  - Customer Service Agent: Handle inquiries and provide support
  - Content Creation Agent: Generate creative content

- 💬 **Interactive Chat Interface**
  - Modern, responsive UI
  - Chat history management
  - Real-time agent responses
  - File upload and analysis

- 📊 **Data Analysis Dashboard**
  - Interactive visualizations
  - Statistical analysis
  - Data insights generation
  - Export capabilities

## Prerequisites

- Python 3.8 or higher
- Streamlit
- Google Cloud credentials (for Gemini AI)
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/multiagentai21.git
cd multiagentai21
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with:
```
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_APPLICATION_CREDENTIALS=path_to_your_credentials.json
```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Open your browser and navigate to:
```
http://localhost:8501
```

3. Select an agent and start interacting!

## Project Structure

```
multiagentai21/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── src/               # Source code
│   ├── agent_core.py  # Core agent functionality
│   └── data_analysis.py # Data analysis tools
├── chat_history/      # Chat history storage
└── README.md         # This file
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for the AI capabilities
- Streamlit for the web interface
- All contributors and users of the project 