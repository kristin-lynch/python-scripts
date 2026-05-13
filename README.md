# Python Scripts

A collection of Python automation scripts for file management and data processing.

## Setup

**Requirements:** Python 3.x

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Scripts

### PDF Renaming

| Script | Description |
|--------|-------------|
| `rename_pdfs.py` | Extracts "Name of User" from Mercyhurst Prep PDFs and renames files |
| `rename_employeename_pdfs.py` | Renames PDFs based on employee name |
| `rename_employeehandbook_pdfs.py` | Renames employee handbook PDFs |
| `rename_nameofuser_pdfs.py` | Renames PDFs based on extracted user name field |
| `batch_rename_pdfs.py` | Batch renames multiple PDFs |
| `batch_rename_folders_files_lowercase.py` | Batch renames folders and files to lowercase |
| `batch_rename_report_cards.py` | Batch renames report card PDFs |

### Data Processing

| Script | Description |
|--------|-------------|
| `consolidate_jamf_records.py` | Consolidates Jamf MDM records |

### Alfred Workflows

| File | Description |
|------|-------------|
| `pwgen.alfredworkflow` | Alfred workflow for generating passwords via genpass |

### Network

| Script | Description |
|--------|-------------|
| `network_scanner.py` | Wraps nmap to discover hosts and open ports on a local network |

**Usage:**
```bash
# Basic scan (top 100 ports) — auto-detects your subnet
python network_scanner.py
```

Scan types can be changed in the script:
- `ping` — host discovery only (fastest)
- `basic` — top 100 ports (default)
- `full` — all 65,535 ports (slowest)

**Requires:** `nmap` (`brew install nmap`)

#### Sample Scan Results (2026-05-13)

Subnet: `10.100.0.0/24` — 1 host found:

| Host | Port | Service |
|------|------|---------|
| 10.100.0.45 (local Mac) | 22/tcp | SSH |
| 10.100.0.45 (local Mac) | 88/tcp | Kerberos |
| 10.100.0.45 (local Mac) | 445/tcp | SMB (file sharing) |
| 10.100.0.45 (local Mac) | 5000/tcp | UPnP |
| 10.100.0.45 (local Mac) | 5900/tcp | VNC (screen sharing) |

## Tools

### genpass

A fast command-line password generator written in Rust.

**Install:**
```bash
cargo install genpass
```

**Usage:**
```bash
genpass                  # 32-char password (default)
genpass 20               # 20-char password
genpass -l -n 16         # lowercase + numbers, 16 chars
genpass -u -l -n -s      # all character types
genpass --passphrase 40  # passphrase of at least 40 chars
```

**Example output:**
```
$ genpass
zvl2@lY0C7Nt7o;|?S[O)gen)wc{25,A
```

**Flags:**
- `-u` / `--include-uppercase`
- `-l` / `--include-lowercase`
- `-n` / `--include-numeric`
- `-s` / `--include-special`
- `--passphrase` — generate a passphrase instead of a password
