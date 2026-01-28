# 🏭 Retrofit Recommender

AI-powered product recommendation system for industrial equipment retrofits using Hugging Face LLMs.

## Features

- **Smart Diagnosis**: Analyzes error logs and device specifications
- **Product Matching**: Recommends compatible replacement parts from catalog
- **Safety Alerts**: Detects voltage/pressure mismatches
- **Secure Token Storage**: Uses `.env` file for API credentials

## Tech Stack

- **Streamlit**: Web interface
- **LangChain**: LLM orchestration
- **Hugging Face**: Meta Llama-3.1-8B model
- **Python 3.14+**

## Quick Start

### 1. Clone & Setup

```bash
cd Retrofit-Recommender
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Token

Edit `.env` file and add your Hugging Face token:

```env
HUGGINGFACE_API_TOKEN=hf_your_token_here
```

Get your token at: https://huggingface.co/settings/tokens

### 3. Run the App

```bash
streamlit run app.py
```

Visit `http://localhost:8502` in your browser.

## Usage

1. Select a scenario (Efficiency Upgrade or Safety Risk)
2. Review/edit the error log and device specs
3. Click "Analyze with Hugging Face"
4. View AI-generated diagnosis and product recommendation

## Project Structure

```
├── app.py              # Main Streamlit application
├── .env                # API token (gitignored)
├── requirements.txt    # Python dependencies
├── test_env.py         # Token verification script
└── README.md          # This file
```

## License

MIT

## Developer

Raka Adrianto, Product Manager Sustainability / AI ML
- LinkedIn: https://www.linkedin.com/in/lugasraka/
- GitHub: https://github.com/lugasraka