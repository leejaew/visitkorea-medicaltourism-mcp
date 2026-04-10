# visitkorea-medicaltourism-mcp

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-SSE-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Overview

An MCP (Model Context Protocol) server that wraps the **Korea Tourism Organization Medical Tourism Information Open API** (`MdclTursmService`). It exposes 8 structured tools consumable by AI agents such as **Manus AI** and **Claude** via SSE (Server-Sent Events) transport.

Data source: [한국관광공사 의료관광정보서비스 (MdclTursmService)](https://www.data.go.kr/data/15143913/openapi.do)  
Data refresh cycle: Once daily | Dev limit: 1,000 requests/day

---

## Available Tools

| Tool | Operation | Description |
|---|---|---|
| `get_ldong_code` | `ldongCode` | Retrieve legal administrative district (법정동) codes for provinces and cities |
| `get_area_based_list` | `areaBasedList` | List medical tourism facilities filtered by administrative region |
| `get_location_based_list` | `locationBasedList` | Find facilities within a GPS radius (max 20 km) |
| `search_medical_by_keyword` | `searchKeyword` | Search facilities by keyword |
| `get_medical_sync_list` | `mdclTursmSyncList` | Full sync list with display status and legacy content ID mapping |
| `get_detail_common` | `detailCommon` | Common detail: title, address, GPS, phone, homepage, overview |
| `get_detail_intro` | `detailIntro` | Intro detail: hours, rest days, parking, capacity, age range |
| `get_detail_medical` | `detailMdclTursm` | Medical detail: specialties, languages, reservation status, SNS |

---

## Setup & Installation

### Prerequisites

- Python 3.11+
- A valid `serviceKey` (Decoding key) from [data.go.kr](https://www.data.go.kr/data/15143913/openapi.do)

### Replit Secrets Configuration

Add the following secret in Replit's Secrets tab:

| Secret Name | Value |
|---|---|
| `VISITKOREA_API_KEY` | Your **일반 인증키 (Decoding)** key from data.go.kr |

> ⚠️ Use the **Decoding key**, NOT the Encoding key. The `requests` library will double-encode an Encoding key, causing `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`.

### Local Development

```bash
# Clone the repo
git clone https://github.com/leejaew/visitkorea-medicaltourism-mcp
cd visitkorea-medicaltourism-mcp

# Install dependencies
pip install -r requirements.txt

# Copy and fill in the env file
cp .env.example .env
# Edit .env and set VISITKOREA_API_KEY=<your_decoding_key>

# Run the server
python main.py
```

The server starts on `http://0.0.0.0:8000` (or `$PORT` if set).

---

## MCP Connector JSON

To connect this server to **Manus AI** or **Claude**, paste the following JSON into the custom connector settings, replacing the URL with your Replit project's public URL:

```json
{
  "mcpServers": {
    "visitkorea-medicaltourism": {
      "url": "https://<your-replit-url>/sse",
      "type": "sse"
    }
  }
}
```

---

## API Reference

Full API documentation: [https://www.data.go.kr/data/15143913/openapi.do](https://www.data.go.kr/data/15143913/openapi.do)

**Base URL:** `https://apis.data.go.kr/B551011/MdclTursmService`

---

## Language Codes

| Code | Language |
|---|---|
| `ENG` | English |
| `JPN` | Japanese |
| `CHS` | Simplified Chinese |
| `RUS` | Russian |

---

## Error Handling

All tools surface API errors as Python exceptions with descriptive messages:

| Code | Type | Behaviour |
|---|---|---|
| `00` / `0000` | Normal | Returns results |
| `03` | No data | Returns `[]` (not an error) |
| `10` | Invalid parameter | `ValueError` with parameter hint |
| `11` | Missing required parameter | `ValueError` with detail |
| `22` | Rate limit exceeded | `RuntimeError` |
| `30` | Service key not registered | `PermissionError` |
| `31` | Key expired | `PermissionError` |

---

## License

MIT
