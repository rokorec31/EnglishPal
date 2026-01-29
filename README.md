# EnglishPal - AI English Learning Companion

EnglishPal is a smart LINE Bot designed to help you improve your English skills. It leverages Google's **Gemini 3.0 Flash** model to provide real-time grammar corrections and translations.

## Features

- **Smart Language Detection**: Automatically identifies whether your input is English or another language (e.g., Chinese).
- **Grammar Correction**: If you type in English, it checks your grammar, provides a corrected version, and explains the mistakes.
- **Translation**: If you type in another language, it naturally translates the text into English.
- **Microservice Ready**: Built with Flask and Gunicorn, Docker-ready for easy deployment.

## Tech Stack

- **Python 3.12**
- **Flask**: Web framework
- **LINE Bot SDK**: Interface with LINE Messaging API
- **Google Generative AI (Gemini 3.0 Flash)**: AI engine for logic
- **LangDetect**: Robust language identification
- **Caddy**: Reverse proxy & Automatic HTTPS
- **Docker & Docker Compose**: Containerization

## Prerequisites

- Python 3.12+
- A LINE Official Account (Messaging API channel)
- A Google Cloud Project with Gemini API enabled
- A Domain name pointing to your server IP (for Caddy)

## Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/your-username/EnglishPal.git
    cd EnglishPal
    ```

2.  **Set up Environment Variables**
    Create a `.env` file in the root directory with the following keys:
    ```ini
    LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token
    LINE_CHANNEL_SECRET=your_channel_secret
    GEMINI_API_KEY=your_gemini_api_key
    ```

3.  **Install Dependencies**
    Using a virtual environment is recommended:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

4.  **Configure Caddy (Optional)**
    If you are deploying to production, edit the `Caddyfile` to replace `englishpal.apiolink.com` with your actual domain name:
    ```
    your-domain.com {
        reverse_proxy englishpal:8000
    }
    ```

## Usage

### Local Development

Run the Flask application locally:
```bash
python app.py
```
*Note: You will need a tunneling service like [ngrok](https://ngrok.com/) to expose your localhost to LINE's Webhook URL.*

### Docker & AWS ECR

1.  **Build and Push Image**
    If you have AWS CLI configured and permissions to push to ECR:
    ```bash
    # Login to ECR
    aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/registry_alias

    # Build the image
    docker build -t englishpal .

    # Tag the image
    docker tag englishpal:latest public.ecr.aws/registry_alias/englishpal:latest

    # Push to ECR
    docker push public.ecr.aws/registry_alias/englishpal:latest
    ```

2.  **Run with Docker Compose**
    Once the image is pushed (or if you just want to pull the latest):
    ```bash
    docker-compose up -d
    ```

## Testing

### Unit Tests
Run the unit tests to verify the grammar checker logic:
```bash
source .venv/bin/activate
python tests/test_grammar_checker.py
```

### Integration Verification
Verify your real API connections (Gemini & LINE) using the verification script:
```bash
source .venv/bin/activate
python tests/verify_integration.py
```

## Project Structure

```
.
├── app.py                  # Main Flask application
├── grammar_checker.py      # Core logic for grammar checking
├── Caddyfile               # Caddy web server configuration
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker build instructions
├── docker-compose.yml      # Docker Compose configuration
├── tests/
│   ├── test_grammar_checker.py  # Unit tests
│   └── verify_integration.py    # Integration verification script
└── README.md               # Project documentation
```

## License

[MIT](LICENSE)
