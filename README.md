# Xiaomi 5G CPE Pro - Automated Reboot

This project provides a robust, containerized solution to automatically reboot a Xiaomi 5G CPE Pro router. It uses Selenium to simulate user interaction with the router's web administration interface, navigating through the login and menu systems to trigger a system reboot.

The entire process is packaged within Docker containers, making it portable, reproducible, and easy to schedule as a one-shot task (e.g., via a cron job or in a CI/CD pipeline).

## Features

-   **Fully Containerized**: Runs entirely within Docker using `docker-compose`. No need to install Python or browser drivers on the host machine.
-   **Reliable Exit Codes**: Propagates the application's exit code, making it ideal for scripting and automated workflows.
-   **Secure by Design**:
    -   Sensitive information like the router password is managed via a `.env` file, not hardcoded in source control.
    -   The application runs as a **non-root user** inside the container.
-   **Efficient Image**: A **multi-stage Dockerfile** creates a small final image, containing only the necessary runtime dependencies.
-   **Persistent Error Logging**: On failure, the script saves a screenshot and the page's HTML source to a Docker volume for easy debugging.
-   **Configurable**: All key parameters (URLs, credentials, error paths) are configured via environment variables.

## Prerequisites

-   [Docker](https://docs.docker.com/get-docker/)
-   [Docker Compose](https://docs.docker.com/compose/install/)

## Setup

1.  **Clone or Download Files**:
    Place `docker-compose.yml`, `Dockerfile`, `main.py`, and `requirements.txt` in a directory on your system.

    ```
    mkdir xiaomi-reboot && cd xiaomi-reboot
    # 
    ```

2.  **Create the Environment File**:
    Create a file named `.env` in the same directory. This file will hold your router's specific details.

    **`.env` file:**
    ```
    # .env

    # The admin URL for your Xiaomi router
    ROUTER_ADMIN_URL=http://192.168.31.1/

    # The admin password for your router
    ROUTER_PASSWORD=your_super_secret_password

    # The IP address of the router (can be the same as the host in the admin URL)
    ROUTER_IP=192.168.31.1
    ```

3.  **Update `.env`**:
    Edit the `.env` file with your router's actual admin URL and password.

## Usage

To run the reboot process, use the following command. It builds the image if needed, ensures fresh containers are used, and most importantly, it returns an exit code of `0` on success or `1` on failure, making it perfect for automation.

```
# Recommended command for both manual and automated runs
docker compose up --build --force-recreate --exit-code-from app
```

-   `--build`: Rebuilds the `app` image if the `Dockerfile` or source code has changed.
-   `--force-recreate`: Ensures containers are recreated from the image every time for a clean run.
-   `--exit-code-from app`: Makes `docker-compose` return the exit code from the `app` container.

## Configuration

The application is configured using environment variables set in the `.env` file and the `docker-compose.yml` file.

#### User-configurable (`.env` file)

| Variable           | Description                                    | Example                      |
| ------------------ | ---------------------------------------------- | ---------------------------- |
| `ROUTER_ADMIN_URL` | The full URL to your router's administration page. | `http://192.168.31.1/`       |
| `ROUTER_PASSWORD`  | The admin password for your router.            | `yoursupersecretpassword`    |
| `ROUTER_IP`        | The IP address of the router.                  | `192.168.31.1`               |

#### Service Configuration (`docker-compose.yml`)

| Variable              | Description                                                                                                   | Default Value                      |
| --------------------- | ------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| `SELENIUM_REMOTE_URL` | The internal URL for the app container to connect to the Selenium container. You should not need to change this. | `http://selenium:4444/wd/hub`      |
| `DEBUG_PAUSE_SECONDS` | On error, the number of seconds to pause before exiting. Useful for live debugging.                             | `30`                               |
| `ERROR_ARTIFACTS_DIR` | The absolute path inside the container where error files (screenshot, source) are saved.                        | `/app/errors`                      |

## Error Handling and Debugging

If the script fails, it will save a screenshot and the page's HTML source to the Docker volume named `xiaomi-reboot_error_output`. To retrieve these files:

```

## Automation with Cron

Using `--exit-code-from` makes the cron job setup much cleaner and more reliable.

1.  Open your crontab for editing:
    ```
    crontab -e
    ```

2.  Add the following line, using absolute paths. This runs the job and logs the output.

    ```
    # Reboot the Xiaomi router every day at 6:00 AM
    0 6 * * * docker compose up -f /path/to/your/xiaomi-reboot --force-recreate --exit-code-from app >> /var/log/xiaomi-reboot.log 2>&1
    ```