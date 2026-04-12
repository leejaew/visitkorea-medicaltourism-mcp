# VisitKorea Medical Tourism MCP Server

![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)
![MCP Transport](https://img.shields.io/badge/MCP-Streamable_HTTP-8B5CF6)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An MCP (Model Context Protocol) server that wraps the **Korea Tourism Organization (KTO) Medical Tourism Open API** (`MdclTursmService`), exposing 8 structured tools that AI agents — including Claude and Manus AI — can call directly via Streamable HTTP.

The underlying data is curated by the **Korea Tourism Organization (KTO)** and published as an Open API on [data.go.kr](https://www.data.go.kr/data/15143913/openapi.do) (Korea's Public Data Portal) under service ID `15143913`. It covers KTO-certified medical tourism facilities across South Korea — hospitals, specialist clinics, and wellness centres — with multilingual support for 5 international languages.

## Features

- **Area-based search** — list facilities by province or city/county
- **Location-based search** — find facilities within a GPS radius (up to 20 km), using WGS84 coordinates
- **Keyword search** — full-text search across all regions
- **Sync list** — full dataset synchronisation list for building and maintaining local databases
- **Detail records** — common info, introductory info (hours, parking, capacity), and medical-specific info (specialties, languages, reservation status)
- **8 MCP tools** — one per API operation, with full parameter documentation in docstrings
- **5 languages** — English, Japanese, Simplified Chinese, Korean, Russian
- **TTL response cache** — district codes cached 24 h; all other responses cached 5 min (≈6× speedup on cache hits)
- **Rate limiter** — 10 upstream calls/min, burst of 5; fast-fail design returns an immediate error when the limit is hit rather than blocking
- **Input validation** — all parameters validated before the upstream request; GPS bounds, date format, sort codes, and language codes checked with clear error messages
- **Health endpoint** — `GET /healthz` for production liveness probes

## Prerequisites

- Python 3.11+
- A valid API key from [data.go.kr](https://www.data.go.kr/data/15143913/openapi.do) (service ID `15143913`)
- Replit account (for deployment)

## Installation & Setup

### 1. Get an API key

1. Visit [https://www.data.go.kr/data/15143913/openapi.do](https://www.data.go.kr/data/15143913/openapi.do)
2. Sign in or create a 공공데이터포털 account
3. Click **활용신청** (Request API access) for service `MdclTursmService`
4. After approval (~10 minutes), retrieve your key from My Page

Either key variant works — the server normalises both automatically at startup:

| Key variant | Where to find it | Notes |
|---|---|---|
| 일반 인증키 **(Encoding)** | My Page → 발급받은 키 | URL-percent-encoded; the server decodes it once before use |
| 일반 인증키 **(Decoding)** | My Page → 발급받은 키 | Raw base64; used as-is |

### 2. Set the Replit Secret

Open the **Secrets** tab in Replit and add:

| Secret name | Value |
|---|---|
| `VISITKOREA_API_KEY` | Your API key (Encoding or Decoding variant — either works) |

### 3. Install dependencies

Replit handles this automatically on first run. To install manually:

```bash
pip install -r mcp-server/requirements.txt
```

**`requirements.txt`:**
```
mcp[cli]
httpx
python-dotenv
```

### 4. Run the server

```bash
python mcp-server/main.py
```

The server starts on the `PORT` environment variable (default `8000`).

| Endpoint | Description |
|---|---|
| `POST /mcp` | Streamable HTTP MCP endpoint (all tool calls) |
| `GET /healthz` | Liveness probe — returns `{"status":"ok","server":"visitkorea-medicaltourism"}` |

## Connecting an AI Agent

### Connector JSON

Paste this into your AI agent's custom connector settings:

```json
{
  "mcpServers": {
    "visitkorea-medicaltourism": {
      "url": "https://<your-replit-url>/mcp"
    }
  }
}
```

Replace `<your-replit-url>` with your deployed Replit project domain.

### Manus AI

Go to **Settings → Connectors → Add Connectors → Custom MCP**, click **Import by JSON**, and paste the JSON above. Do not add a `"type"` field — Manus AI infers Streamable HTTP from the URL automatically.

### Claude Desktop

Add the JSON to your `claude_desktop_config.json` under the `"mcpServers"` key.

## Tool Reference

All tools follow the same call pattern — they accept a `lang_div_cd` and return a list of dicts. Pagination defaults to 10 results per page starting at page 1.

### Recommended workflows

| Goal | Sequence |
|---|---|
| Search by region | `get_ldong_code` → `get_area_based_list` → `get_detail_common` / `get_detail_medical` |
| Search near a location | `get_location_based_list` → `get_detail_common` / `get_detail_medical` |
| Search by keyword | `search_medical_by_keyword` → `get_detail_common` / `get_detail_medical` |
| Build a local database | `get_medical_sync_list` |

---

### Tool 1 — `get_ldong_code`

Retrieve legal administrative district (법정동) codes for province/city and district filtering.

**Upstream endpoint:** `GET /ldongCode`  
**Cache TTL:** 24 hours (codes are static reference data)

| Parameter | Type | Required | Description |
|---|---|---|---|
| `lang_div_cd` | string | Optional | Language code (default `ENG`) |
| `l_dong_regn_cd` | string | Optional | Province code — e.g. `11` = Seoul. Omit to list all provinces. |
| `l_dong_list_yn` | string | Optional | `N` = 시도/시군구 codes only (default); `Y` = full 법정동 list |
| `num_of_rows` | int | Optional | Results per page — clamped to 1–100 (default 10) |
| `page_no` | int | Optional | Page number (default 1) |

**Example response item:**
```json
{ "rnum": 1, "code": "11", "name": "Seoul" }
```

---

### Tool 2 — `get_area_based_list`

List medical tourism facilities filtered by administrative region.

**Upstream endpoint:** `GET /areaBasedList`  
**Cache TTL:** 5 minutes

| Parameter | Type | Required | Description |
|---|---|---|---|
| `lang_div_cd` | string | Optional | Language code |
| `arrange` | string | Optional | Sort order: `A`=title, `C`=modified, `D`=created, `O`/`Q`/`R`=image-only variants |
| `l_dong_regn_cd` | string | Optional | Province code from `get_ldong_code` |
| `l_dong_signgu_cd` | string | Optional | District code (requires `l_dong_regn_cd`) |
| `mdfcn_dt` | string | Optional | Modified-since date filter in **YYYYMMDD** format |
| `num_of_rows` | int | Optional | Results per page (default 10) |
| `page_no` | int | Optional | Page number (default 1) |

---

### Tool 3 — `get_location_based_list`

Find medical tourism facilities within a GPS radius. Coordinates must be within South Korea's WGS84 bounding box (longitude 124–132, latitude 33–39).

**Upstream endpoint:** `GET /locationBasedList`  
**Cache TTL:** 5 minutes

| Parameter | Type | Required | Description |
|---|---|---|---|
| `lang_div_cd` | string | Optional | Language code |
| `map_x` | float | **Required** | Longitude in WGS84 — e.g. `126.9780` (Seoul) |
| `map_y` | float | **Required** | Latitude in WGS84 — e.g. `37.5665` (Seoul) |
| `radius` | int | **Required** | Search radius in metres — 1 to 20,000 |
| `arrange` | string | Optional | Sort: `E`=distance asc, `S`=distance desc+image; or standard A/C/D/O/Q/R |
| `l_dong_regn_cd` | string | Optional | Optional province filter |
| `l_dong_signgu_cd` | string | Optional | Optional district filter (requires `l_dong_regn_cd`) |
| `mdfcn_dt` | string | Optional | Modified-since date filter in **YYYYMMDD** format |
| `num_of_rows` | int | Optional | Results per page (default 10) |
| `page_no` | int | Optional | Page number (default 1) |

Response items include a `dist` field (distance in metres from the provided coordinates).

---

### Tool 4 — `search_medical_by_keyword`

Full-text keyword search across all medical tourism facilities.

**Upstream endpoint:** `GET /searchKeyword`  
**Cache TTL:** 5 minutes

| Parameter | Type | Required | Description |
|---|---|---|---|
| `lang_div_cd` | string | Optional | Language code |
| `keyword` | string | **Required** | Search term (automatically URL-encoded) |
| `arrange` | string | Optional | Sort order (A/C/D/O/Q/R) |
| `l_dong_regn_cd` | string | Optional | Province filter |
| `l_dong_signgu_cd` | string | Optional | District filter (requires `l_dong_regn_cd`) |
| `num_of_rows` | int | Optional | Results per page (default 10) |
| `page_no` | int | Optional | Page number (default 1) |

---

### Tool 5 — `get_medical_sync_list`

Retrieve the full medical tourism synchronisation list. Use for building or refreshing a local database of all facilities.

**Upstream endpoint:** `GET /mdclTursmSyncList`  
**Cache TTL:** 5 minutes

| Parameter | Type | Required | Description |
|---|---|---|---|
| `lang_div_cd` | string | Optional | Language code |
| `showflag` | string | Optional | `1` = publicly visible only; `0` = hidden only |
| `old_content_id` | string | Optional | Last known content ID — fetch only newer records |
| `mdfcn_dt` | string | Optional | Modified-since date in **YYYYMMDD** format |
| `num_of_rows` | int | Optional | Results per page (default 10) |
| `page_no` | int | Optional | Page number (default 1) |

---

### Tool 6 — `get_detail_common`

Fetch full common detail for a specific facility: title, address, GPS, phone, homepage, and overview text.

**Upstream endpoint:** `GET /detailCommon`  
**Cache TTL:** 5 minutes

| Parameter | Type | Required | Description |
|---|---|---|---|
| `lang_div_cd` | string | Optional | Language code |
| `content_id` | string | **Required** | Content ID returned by any list or search tool |
| `num_of_rows` | int | Optional | Results per page (default 1) |
| `page_no` | int | Optional | Page number (default 1) |

**Key response fields:** `contentId`, `title`, `overview`, `homepage`, `tel`, `baseAddr`, `detailAddr`, `zipCd`, `mapX`, `mapY`, `orgImage`, `thumbImage`, `lDongRegnCd`, `lDongSignguCd`, `regDt`, `mdfcnDt`

> **Note:** The upstream API returns GPS fields as lowercase `mapx`/`mapy`. This tool normalises them to `mapX`/`mapY` for consistency with the list-endpoint field names.

---

### Tool 7 — `get_detail_intro`

Fetch type-specific introductory details: opening hours, rest days, parking, capacity, and age suitability.

**Upstream endpoint:** `GET /detailIntro`  
**Cache TTL:** 5 minutes

| Parameter | Type | Required | Description |
|---|---|---|---|
| `lang_div_cd` | string | Optional | Language code |
| `content_id` | string | **Required** | Content ID |
| `num_of_rows` | int | Optional | Results per page (default 1) |
| `page_no` | int | Optional | Page number (default 1) |

---

### Tool 8 — `get_detail_medical`

Fetch medical-specific details: specialties, foreign languages served, reservation status, and SNS info.

**Upstream endpoint:** `GET /detailMdclTursm`  
**Cache TTL:** 5 minutes

| Parameter | Type | Required | Description |
|---|---|---|---|
| `lang_div_cd` | string | Optional | Language code |
| `content_id` | string | **Required** | Content ID |
| `num_of_rows` | int | Optional | Results per page (default 1) |
| `page_no` | int | Optional | Page number (default 1) |

**Key response fields:** `mainMdclSubjInfo` (main specialties), `svcLangInfo` (supported languages), `onlineRsvtPsblYn` (online reservation available)

---

## Language Code Reference

| Code | Language |
|---|---|
| `ENG` | English |
| `JPN` | Japanese (日本語) |
| `CHS` | Simplified Chinese (简体中文) |
| `KOR` | Korean (한국어) |
| `RUS` | Russian (Русский) |

## Error Handling

### Upstream API errors

Tool functions surface data.go.kr errors as Python exceptions with descriptive messages. The raw API key is masked (`[REDACTED]`) in all error strings before they leave the process.

| Upstream code | Exception type | Meaning |
|---|---|---|
| `00` / `0000` | — | Success; returns results |
| `03` | — | No data; returns `[]` |
| `10` | `ValueError` | Invalid request parameter |
| `11` | `ValueError` | Missing required parameter |
| `22` | `RuntimeError` | Upstream daily quota (1,000 requests/day) exceeded |
| `30` | `PermissionError` | Service key not registered |
| `31` | `PermissionError` | Service key expired |
| other | `RuntimeError` | Unexpected API error with code and message |

### Local rate limiter

The server enforces a **10 calls/minute** limit (burst of 5) on requests that reach the upstream API. Cache hits bypass the limiter entirely. When the limit is exceeded, the tool returns immediately with:

```
Rate limit: too many requests to upstream API. Please retry after Xs.
(Limit: 10 calls/min, burst 5)
```

This is a fast-fail design — no blocking sleep — so the agent receives the retry-after guidance instantly and can back off gracefully.

## Project Structure

```
visitkorea-medicaltourism-mcp/
├── mcp-server/
│   ├── main.py                  # FastMCP entrypoint — Streamable HTTP, /healthz endpoint
│   ├── requirements.txt         # mcp[cli], httpx, python-dotenv
│   ├── README.md
│   ├── tools/
│   │   ├── ldong_code.py        # get_ldong_code
│   │   ├── area_based_list.py   # get_area_based_list
│   │   ├── location_based_list.py # get_location_based_list
│   │   ├── search_keyword.py    # search_medical_by_keyword
│   │   ├── sync_list.py         # get_medical_sync_list
│   │   ├── detail_common.py     # get_detail_common
│   │   ├── detail_intro.py      # get_detail_intro
│   │   └── detail_mdcl_tursm.py # get_detail_medical
│   └── utils/
│       ├── config.py            # API key loading, FIXED_PARAMS, key masking
│       ├── cache.py             # TTL dict cache (24h / 5min by endpoint)
│       ├── rate_limiter.py      # Token bucket — 10/min, burst 5, fast-fail
│       ├── api_client.py        # call_api() — wires cache, limiter, httpx, retry
│       └── validation.py        # Input validation for all parameter types
└── artifacts/
    ├── landing/                 # Developer landing page (React + Vite)
    └── api-server/              # Express proxy (CORS, /api/healthz)
```

### `utils/` module responsibilities

Each module has a single, clearly bounded responsibility:

| Module | LOC | Responsibility |
|---|---|---|
| `config.py` | 41 | Loads `VISITKOREA_API_KEY` at import time, normalises Encoding/Decoding variant, exposes `FIXED_PARAMS` and `mask_key()` |
| `cache.py` | 49 | SHA-256-keyed TTL dict cache; `make_key`, `get`, `set`, `ttl_for` |
| `rate_limiter.py` | 60 | `TokenBucket` class; module-level `limiter` singleton used by `call_api` |
| `api_client.py` | 141 | `call_api(endpoint, params, num_of_rows, page_no)` — the only public function; handles the full request lifecycle |
| `validation.py` | 93 | `validate_lang`, `validate_pagination`, `validate_gps`, `validate_radius`, `validate_date`, `validate_arrange`, `validate_showflag` |

## Performance

| Scenario | Typical latency |
|---|---|
| Cache hit | < 5 ms |
| Cache miss — first `get_ldong_code` call | ~600 ms (upstream API) |
| Subsequent `get_ldong_code` calls (24h TTL) | < 5 ms |
| Cache miss — other tools | ~600 ms |
| Subsequent calls within 5 min TTL | < 5 ms |

The httpx client maintains a persistent TCP connection pool (`max_connections=10`, `max_keepalive_connections=5`) to avoid TLS handshake overhead on every request. Total request timeout is 15 s; connection timeout is 5 s.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `VISITKOREA_API_KEY` | Yes | API key from data.go.kr (Encoding or Decoding variant) |
| `PORT` | No | Port for uvicorn to listen on (default `8000`) |

## Contributing

Contributions are welcome. Please open an issue before submitting a pull request. Ensure all changes are tested against the live API and that no API keys are committed to the repository.

## License

MIT License

Tourism data provided by the Korea Tourism Organization (KTO) via the 공공데이터포털 open API platform (`data.go.kr`). Data usage is subject to KTO terms — attribution is required for `Type1` content; `Type3` content additionally prohibits modification.
