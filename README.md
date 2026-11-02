# # CoordinX — AI-Powered Coordinated Behavior Detection System

**CoordinX** is an AI-powered social media analysis system designed to identify suspicious coordinated behavior and potential buzzer networks on X (formerly Twitter).

The system analyzes publicly accessible post data and account activity patterns to identify similarities in content, temporal behavior, and relationships between accounts.

By combining Natural Language Processing (NLP), Deep Learning, and Graph Neural Networks (GNN), CoordinX aims to provide a more comprehensive analysis of potentially coordinated social media activities.

## Key Features

- **Text Analysis:** Analyzes Indonesian social media content using IndoBERTweet.
- **Temporal Behavior Analysis:** Identifies suspicious posting patterns using LSTM.
- **Graph-Based Analysis:** Examines relationships and potential coordination between accounts using GraphSAGE.
- **Account-Level Detection:** Estimates whether an account exhibits suspicious coordination patterns.
- **Group-Level Detection:** Identifies clusters of accounts that may exhibit coordinated behavior.
- **Telegram Bot Integration:** Allows users to submit an X post URL and receive an analysis report.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| NLP Model | IndoBERTweet |
| Temporal Model | LSTM |
| Graph Neural Network | GraphSAGE |
| Deep Learning Framework | PyTorch |
| NLP Framework | Hugging Face Transformers |
| Graph Processing | PyTorch Geometric, NetworkX |
| Data Processing | Pandas, NumPy |
| Backend API | FastAPI |
| User Interface | Telegram Bot |
| Development Environment | Google Colab |

## System Architecture

CoordinX combines three main analytical components:

1. **IndoBERTweet** — Extracts semantic representations from social media posts.
2. **LSTM** — Learns temporal patterns from account activity sequences.
3. **GraphSAGE** — Learns relationships and structural patterns between accounts.

The extracted features are combined through a feature fusion architecture and processed by classification layers for account-level and group-level analysis.

## Project Objectives

- Develop an AI-based approach to analyze suspicious coordinated activities on social media.
- Identify patterns that may indicate coordinated inauthentic behavior.
- Explore the combination of NLP, temporal analysis, and graph learning.
- Provide accessible analysis through a Telegram Bot interface.
- Support social media literacy and research through evidence-based analysis.

## Important Disclaimer

CoordinX is a research and educational project. Its predictions indicate potential suspicious patterns and do not independently establish that an account or group is a buzzer, bot, or malicious actor.

Coordinated behavior does not necessarily mean inauthentic behavior. All findings should be interpreted with appropriate context, supporting evidence, and limitations of the available data.

## Project Status

Currently under development as part of a social cyber-themed Hackathon project.
