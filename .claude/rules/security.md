# Security Rules

## Non-Negotiable Rules

### 1. No Hardcoded Secrets
```python
# NEVER
API_KEY = "sk-12345..."
PASSWORD = "hunter2"

# ALWAYS
import os
API_KEY = os.environ.get("API_KEY")
```

### 2. No Secrets in Git
```gitignore
# .gitignore MUST include:
.env*
*.key
*.pem
credentials*
*_secret*
```

### 3. Environment Variables for Credentials
```bash
# .env (never committed)
ANTHROPIC_API_KEY=...
GARMIN_USERNAME=...
GARMIN_PASSWORD=...
USDA_API_KEY=...
```

## Input Validation

### Voice Commands
Voice input must be sanitized before any processing.
```python
# CORRECT
def handle_voice(text: str) -> str:
    # Strip and normalize
    text = text.strip().lower()
    # Validate against known patterns
    if not VALID_COMMAND_PATTERN.match(text):
        return "I didn't understand that."
    return process_command(text)
```

### File Paths
Never trust user-provided paths.
```python
# CORRECT
from pathlib import Path

def read_file(filename: str) -> str:
    base = Path.home() / ".atlas" / "data"
    path = (base / filename).resolve()
    # Prevent directory traversal
    if not str(path).startswith(str(base)):
        raise ValueError("Invalid path")
    return path.read_text()

# WRONG
def read_file(filename: str) -> str:
    return open(filename).read()  # User could pass ../../../etc/passwd
```

### Shell Commands
Never interpolate user input into shell commands.
```python
# CORRECT
import subprocess
subprocess.run(["ls", "-la", directory], check=True)

# WRONG
import os
os.system(f"ls -la {directory}")  # Command injection risk
```

## Database Security

### Always Parameterize
```python
# CORRECT
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# WRONG
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

### Limit Query Results
```python
# CORRECT
cursor.execute("SELECT * FROM events LIMIT 100")

# WRONG (could return millions of rows)
cursor.execute("SELECT * FROM events")
```

## WSL2 Bridge Security

### File-Based IPC
The voice bridge uses files for communication:
- `~/.atlas/.bridge/audio_in.raw`
- `~/.atlas/.bridge/audio_out.raw`
- `~/.atlas/.bridge/status.txt`

**Rules:**
1. Validate file existence before reading
2. Don't execute content from bridge files
3. Sanitize all text before processing

### Session Status
`session_status.json` is readable by UI but should not accept commands.
```python
# Read-only pattern
status = json.loads(Path("session_status.json").read_text())
# Never: execute(status["command"])
```

## Logging Security

### Never Log Sensitive Data
```python
# CORRECT
logger.info(f"User authenticated: {username}")

# WRONG
logger.info(f"Login attempt: {username}:{password}")
logger.debug(f"API response: {api_key_included_response}")
```

### Redact in Error Messages
```python
# CORRECT
except APIError as e:
    logger.error(f"API call failed: {e.status_code}")

# WRONG
except APIError as e:
    logger.error(f"API call failed: {e.response_body}")  # May contain secrets
```
