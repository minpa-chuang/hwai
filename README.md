# PHP Network Device Monitor

This simple project provides a basic visual network monitoring tool implemented in PHP. It checks the connectivity of devices by pinging them every five minutes using multiple processes.

## Files

- `devices.json` – list of devices to monitor (`floor`, `ip`, `location`).
- `monitor.php` – CLI script that performs the ping tests in parallel using `pcntl_fork` and writes the latest results to `results.json`.
- `index.php` – web page that displays the last monitoring result.
- `results.json` – automatically generated file holding the last ping results.

## Usage

1. Update `devices.json` with your network devices.
2. Run the monitor script in the background:
   ```bash
   php monitor.php &
   ```
   It will ping each device every 5 minutes sending 3 packets.
3. Serve `index.php` through a web server such as Apache or PHP's built‑in server:
   ```bash
   php -S localhost:8000
   ```
4. Visit `http://localhost:8000/index.php` to see the status page. Green indicator means the device responded to ping; red indicates failure.
