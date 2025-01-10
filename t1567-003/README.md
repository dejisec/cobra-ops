# T1567.003 - Exfiltration Over Web Service: Exfiltration to Text Storage Sites

Implementation of [T1567.003](https://attack.mitre.org/techniques/T1567/003/) - Exfiltration Over Web Service: Exfiltration to Text Storage Sites.

## Use Case

Traffic to popular text storage sites such as `Pastebin[.]com`, `Paste[.]ee`, and `Pastebin[.]pl` could be prevented by enterprise network security controls. However, less popular or custom text storage sites may not be blocked.

Operators can use the implementation in the project to assess the effectiveness of an organization's security controls against exfiltration attempts to text storage sites.

## Usage

1. Install the dependencies:

    ```sh
    python3 -m ven .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2. Run the Flask application:

    ```sh
    gunicorn -w 4 -b localhost:8000 app:app
    # proxy the requests to the gunicorn server with your solution of choice
    # for example cloudfared
    cloudflared tunnel --url http://localhost:8000
    ```