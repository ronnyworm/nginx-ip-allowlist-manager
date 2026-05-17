# Nginx IP Allowlist Manager

A lightweight Python utility to manage temporary IP allowlists for Nginx. It automatically comments out "expired" IP addresses based on metadata comments and reloads Nginx to enforce the new rules.

This is particularly useful for securing legacy applications where you want an extra layer of protection (IP allowlisting) on top of Basic Auth without manually editing configs every few days.

## How it Works

The script parses a specific Nginx configuration file (`allowlist.conf`). It looks for pairs of lines consisting of an **expiry comment** and an **allow directive**:

```nginx
# expire after 2026-12-31
allow 1.2.3.4;
```

If the current system date is past the expiry date, the script transforms the entry into:

```nginx
# expire after 2026-12-31
#allow 1.2.3.4;
```

It then validates the Nginx configuration and reloads the service automatically.

---

## Setup

### 1. Nginx Configuration
Create a file at `/etc/nginx/conf.d/allowlist.conf` and add your IPs:

```nginx
# expire after 2026-06-01
allow 192.168.1.50;

# expire never
allow 1.1.1.1;

deny all;
```

In your main Nginx site configuration (e.g., `/etc/nginx/sites-available/default`), include this file:

```nginx
server {
    listen 443 ssl;
    server_name your-app.com;

    include /etc/nginx/conf.d/allowlist.conf;

    location / {
        proxy_pass http://localhost:3000;
        # ... other proxy settings
    }
}
```

### 2. Script Installation
1. Move `expire_ips.py` to a secure location, such as `/usr/local/bin/`.
2. Ensure it has execution permissions:
   ```bash
   sudo chmod +x /usr/local/bin/expire_ips.py
   ```

---

## Features

*   **Flat Logic:** Uses guard clauses for high readability and maintainability.
*   **Atomic Writes:** Uses a temporary file before overwriting the live config to prevent corruption.
*   **Nginx Safety Check:** Runs `nginx -t` before reloading. If you made a typo in the config, the script will skip the reload to keep your server online.
*   **Indifferent to Formatting:** Skips standard comments, empty lines, and the final `deny all;` directive automatically.

---

## Automation (Cron)

To run the cleanup automatically every night at 1, add a entry to the root crontab:

1. Open crontab: `sudo crontab -e`
2. Add the following line:
   ```bash
   1 0 * * * /usr/bin/python3 /opt/custom/nginx-ip-allowlist-manager/expire_ips.py >> /var/log/nginx-ip-allowlist-manager.log 2>&1
   ```

---

## Requirements
*   **Python 3.x**
*   **Root/Sudo Privileges:** Required to modify Nginx configs and reload the `systemctl` daemon.
*   **Nginx:** Installed and managed via `systemctl`.

## Format Specification
The script expects the following format:
*   Comment line must start exactly with `# expire after ` followed by `YYYY-MM-DD`.
*   The very next line must be the `allow` directive.
*   Use `# expire never` or any other comment format for IPs that should never be touched.
```
