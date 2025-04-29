Deployment (Simplified EC2)
===========================

This application is deployed to a single AWS EC2 instance using Gunicorn and Nginx.

Setup Steps:
------------
1.  An **Ubuntu Server LTS** EC2 instance (t2.micro) is launched.
2.  A **Security Group** is configured to allow inbound traffic on:
    * Port 22 (SSH) from a specific IP for management.
    * Port 80 (HTTP) from anywhere for user access.
3.  Required software is installed: `python3`, `pip`, `venv`, `git`, `nginx`, `gunicorn`.
4.  The application code is cloned from the GitHub repository.
5.  A Python virtual environment (`venv`) is created, and dependencies from `requirements.txt` are installed.
6.  **Gunicorn** is configured to run the Flask application via a **Systemd service** (`/etc/systemd/system/imageprocessor.service`). This service manages the Gunicorn process, runs it as the `ubuntu` user, and makes it communicate via a Unix socket (`imageprocessor.sock`).
7.  **Nginx** is configured as a reverse proxy (`/etc/nginx/sites-available/default`). It listens on port 80, handles incoming HTTP requests, sets necessary proxy headers, increases the max upload size (`client_max_body_size`), and forwards requests to the Gunicorn socket (`proxy_pass`).
8.  The `imageprocessor` systemd service is started and enabled, and Nginx is restarted to apply the configuration.

CI/CD via GitHub Actions
------------------------
The `.github/workflows/ci-cd.yml` file automates testing and deployment:
1.  On pushes to the `main` branch, the workflow checks out the code.
2.  It installs dependencies and runs unit/integration tests (`pytest`) and end-to-end tests (`selenium`).
3.  If tests pass, the `deploy_to_ec2` job connects to the EC2 instance via SSH using credentials stored in GitHub Secrets (`EC2_HOST_IP`, `EC2_SSH_PRIVATE_KEY`).
4.  On the EC2 instance, the job executes a script to:
    * Navigate to the application directory.
    * Pull the latest code from the `main` branch (`git fetch/reset`).
    * Activate the virtual environment.
    * Install/update Python dependencies (`pip install -r requirements.txt`).
    * Restart the Gunicorn service (`sudo systemctl restart imageprocessor`) to load the new code.