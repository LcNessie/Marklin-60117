# Updating the Application

[<< Home](../README.md) | [Installation Guide](INSTALL.md) | [Troubleshooting](TROUBLESHOOTING.md) | [Robustness](ROBUSTNESS.md) | **Updating** | [Changelog](CHANGELOG.md) | [Code of Conduct](CODE_OF_CONDUCT.md)

---

This guide explains how to update the Märklin UDP Bridge to the latest version.

## Update Workflow

The recommended workflow is to download the latest pre-built package and deploy it to your Raspberry Pi.

### Step 1: Download the Latest Release

Download the latest `marklin-bridge-*.tar.gz` package from the project's release page.

> **Placeholder:** `https://github.com/your-username/your-repo/releases/latest`

Once downloaded, transfer the `.tar.gz` file to the home directory of your Raspberry Pi using `scp` or your preferred file transfer tool.

### Step 2: On the Raspberry Pi - Prepare for Update

If you have followed the [Robustness Guide](ROBUSTNESS.md) to make your filesystem read-only, you must temporarily disable it.

1.  Run `sudo raspi-config`.
2.  Navigate to `Performance Options` -> `Overlay File System`.
3.  Select **No** to disable the overlay and reboot when prompted.

### Step 3: On the Raspberry Pi - Install the Update

Extract the archive, update dependencies, and ensure permissions are correct.

```bash
# 1. Extract the archive, overwriting the old files
cd /opt/marklin-bridge
sudo tar -xzvf /home/pi/marklin-bridge-*.tar.gz --strip-components=1 --overwrite

# 2. Update Python dependencies
sudo -u marklin-bridge /opt/marklin-bridge/venv/bin/pip3 install -r /opt/marklin-bridge/requirements.txt

# 3. Ensure file ownership is correct
sudo chown -R marklin-bridge:marklin-bridge /opt/marklin-bridge
```

*Note: Be careful not to overwrite your `config.ini` file unless you intend to.*

### Step 3: Update Dependencies

The new version might have updated dependencies. It's always a good idea to re-run the installation from `requirements.txt`.

On your Raspberry Pi:
```bash
sudo pip3 install -r /opt/marklin-bridge/requirements.txt
```

### Step 4: Restart the Service

Apply the changes by restarting the `systemd` service.

```bash
sudo systemctl restart marklin-bridge.service
```

You can check the status to ensure it started correctly:
```bash
sudo systemctl status marklin-bridge.service
```

### Step 5: Re-enable Read-Only Filesystem (If Applicable)

If you disabled the read-only filesystem in Step 1, you should now re-enable it to protect your system.

1.  Run `sudo raspi-config`.
2.  Navigate to `Performance Options` -> `Overlay File System`.
3.  Select **Yes** to enable the overlay and reboot.