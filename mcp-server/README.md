# VisitKorea Medical Tourism MCP Server

![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)
![MCP Transport](https://img.shields.io/badge/MCP-Streamable_HTTP-8B5CF6)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An MCP (Model Context Protocol) server that wraps the **Korea Tourism Organization (KTO) Medical Tourism Open API** (`MdclTursmService`), exposing 8 structured tools that AI agents — including Claude and Manus AI — can call directly via Streamable HTTP.

The underlying data is curated by the **Korea Tourism Organization (KTO)** and published as an Open API on [data.go.kr](https://www.data.go.kr/data/15143913/openapi.do) (Korea's Public Data Portal) under service ID `15143913`. It covers KTO-certified medical tourism facilities across South Korea — hospitals, specialist clinics, and wellness centres — with multilingual support for 4 international languages.

## Features

- **Area-based search** — list medical tourism facilities by province or city/county
- **Location-based search** — find facilities within a GPS radius (up to 20 km), using WGS84 coordinates
- **Keyword search** — full-text search across all regions
- **Sync list** — full dataset synchronisation list for building and maintaining local databases
- **Detail records** — common info, introductory info (hours, parking, capacity), and medical-specific info (specialties, languages, reservation status)
- **8 MCP tools** — one per API operation, with full parameter documentation in docstrings
- **Multilingual** — 4 languages: English, Japanese, Simplified Chinese, Russian

## Prerequisites

- Python 3.11+
- A valid `serviceKey` (Decoding key) from [data.go.kr](https://www.data.go.kr/data/15143913/openapi.do) (Service ID: `15143913`)
- Replit account (for deployment)

## Installation & Replit Secrets Setup

1. **Clone or fork this repository** into your Replit account.
2. **Obtain your API key** by registering at [https://www.data.go.kr/data/15143913/openapi.do](https://www.data.go.kr/data/15143913/openapi.do).
3. **Set Replit Secrets** — open the Secrets tab in Replit and add:

   | Secret name | Description |
   |-------------|-------------|
   | `VISITKOREA_API_KEY` | Your **일반 인증키 (Decoding)** key from data.go.kr |

   > ⚠️ Use the **Decoding key**, NOT the Encoding key. The `requests` library will double-encode an Encoding key, causing `SERVICE_KEY_IS_NOT_REGISTERED_ERROR`.

4. **Install dependencies** (Replit handles this automatically):
   ```bash
   pip install -r requirements.txt
   ```
5. **Run the server**:
   ```bash
   python main.py
   ```

The server starts on the `PORT` environment variable (default `8000`).
- Landing page: `http://localhost:8000/`
- Streamable HTTP endpoint: `http://localhost:8000/mcp`

## MCP Connector JSON

Paste this into your AI agent's custom connector settings (Claude Desktop, Manus AI, or any MCP-compatible client):

```json
{
  "mcpServers": {
    "visitkorea-medicaltourism": {
      "url": "https://<your-replit-url>/mcp"
    }
  }
}
```

Replace the URL with your own deployed Replit project URL.

**Manus AI:** Go to **Settings → Connectors → Add Connectors → Custom MCP**, then click **Import by JSON** and paste the JSON above (without a `type` field — Manus infers Streamable HTTP from the URL automatically).

## Tool Reference

### Tool 1 — `get_ldong_code`

Retrieve legal administrative district (법정동) codes for province/city and district filtering.

**Endpoint:** `GET /ldongCode`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lang_div_cd` | string | Optional | Language code (default: `ENG`) |
| `num_of_rows` | int | Optional | Results per page (default: 10) |
| `page_no` | int | Optional | Page number (default: 1) |
| `l_dong_regn_cd` | string | Optional | Province/city code (e.g. `11` = Seoul) |
| `l_dong_list_yn` | string | Optional | `N` = 시도/시군구 codes; `Y` = full 법정동 list |

---

### Tool 2 — `get_area_based_list`

List medical tourism facilities filtered by administrative region.

**Endpoint:** `GET /areaBasedList`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lang_div_cd` | string | Optional | Language code |
| `arrange` | string | Optional | Sort order (A/C/D/O/Q/R) |
| `mdfcn_dt` | string | Optional | Modified date filter (YYMMDD) |
| `l_dong_regn_cd` | string | Optional | Province/city code |
| `l_dong_signgu_cd` | string | Optional | District code (requires `l_dong_regn_cd`) |

---

### Tool 3 — `get_location_based_list`

Find medical tourism facilities within a GPS radius. Maximum radius: 20,000 m.

**Endpoint:** `GET /locationBasedList`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `map_x` | float | **Required** | GPS longitude (WGS84) |
| `map_y` | float | **Required** | GPS latitude (WGS84) |
| `radius` | int | **Required** | Search radius in metres (max 20,000) |
| `arrange` | string | Optional | Sort: `E`/`S` = distance; A/C/D/O/Q/R = standard |
| `lang_div_cd` | string | Optional | Language code |

---

### Tool 4 — `search_medical_by_keyword`

Full-text keyword search across all medical tourism facilities.

**Endpoint:** `GET /searchKeyword`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `keyword` | string | **Required** | Search keyword (auto URL-encoded) |
| `lang_div_cd` | string | Optional | Language code |
| `arrange` | string | Optional | Sort order |
| `l_dong_regn_cd` | string | Optional | Province/city code |

---

### Tool 5 — `get_medical_sync_list`

Retrieve the medical tourism synchronisation list for building local datasets.

**Endpoint:** `GET /mdclTursmSyncList`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `showflag` | string | Optional | `1` = publicly visible; `0` = hidden |
| `old_content_id` | string | Optional | Previous content ID for delta sync |
| `mdfcn_dt` | string | Optional | Modified date filter (YYMMDD) |

---

### Tool 6 — `get_detail_common`

Fetch full common detail record: title, address, GPS, phone, homepage, overview.

**Endpoint:** `GET /detailCommon`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content_id` | string | **Required** | Content ID from list results |
| `lang_div_cd` | string | Optional | Language code |

---

### Tool 7 — `get_detail_intro`

Fetch type-specific introductory details: opening hours, rest days, parking, capacity, age suitability.

**Endpoint:** `GET /detailIntro`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content_id` | string | **Required** | Content ID |
| `lang_div_cd` | string | Optional | Language code |

---

### Tool 8 — `get_detail_medical`

Fetch medical-specific details: specialties, foreign languages served, reservation status, SNS info.

**Endpoint:** `GET /detailMdclTursm`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content_id` | string | **Required** | Content ID |
| `lang_div_cd` | string | Optional | Language code |

---

## Language Code Reference

| Code | Language |
|------|----------|
| `ENG` | English |
| `JPN` | Japanese (日本語) |
| `CHS` | Simplified Chinese (简体中文) |
| `RUS` | Russian (Русский) |

## Error Handling

All tools surface API errors as Python exceptions with descriptive messages:

| Code | Type | Behaviour |
|------|------|-----------|
| `00` / `0000` | Normal | Returns results |
| `03` | No data | Returns `[]` (not an error) |
| `10` | Invalid parameter | `ValueError` with parameter hint |
| `11` | Missing required parameter | `ValueError` with detail |
| `22` | Rate limit exceeded | `RuntimeError` |
| `30` | Service key not registered | `PermissionError` |
| `31` | Key expired | `PermissionError` |

## API Key Registration

1. Visit [https://www.data.go.kr/data/15143913/openapi.do](https://www.data.go.kr/data/15143913/openapi.do)
2. Sign in or create a 공공데이터포털 account
3. Click **활용신청** (Request API access) for service `MdclTursmService`
4. After approval (~10 minutes), retrieve your **일반 인증키 (Decoding)** key from My Page
5. Add it to Replit Secrets as `VISITKOREA_API_KEY`

## Project Structure

```
visitkorea-medicaltourism-mcp/
├── mcp-server/
│   ├── main.py              # Replit entrypoint — starts Streamable HTTP MCP server
│   ├── requirements.txt
│   ├── README.md
│   ├── tools/
│   │   ├── ldong_code.py
│   │   ├── area_based_list.py
│   │   ├── location_based_list.py
│   │   ├── search_keyword.py
│   │   ├── sync_list.py
│   │   ├── detail_common.py
│   │   ├── detail_intro.py
│   │   └── detail_mdcl_tursm.py
│   └── utils/
│       └── api_client.py
└── artifacts/
    └── landing/             # Developer landing page (React + Vite)
```

## Contributing

Contributions are welcome. Please open an issue before submitting a pull request. Ensure all changes are tested against the live API and that no API keys are committed to the repository.

## License

MIT License

Tourism data provided by the Korea Tourism Organization (KTO) via the 공공데이터포털 open API platform (`data.go.kr`). Data usage is subject to KTO terms — attribution is required for `Type1` content; `Type3` content additionally prohibits modification.
