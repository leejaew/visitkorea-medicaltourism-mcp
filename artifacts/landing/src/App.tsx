import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "./components/ui/collapsible";

declare const __REPLIT_DOMAINS__: string;

function getDomainInfo(): { host: string; isProd: boolean } {
  // If the page is actually being served from a .replit.app domain, use it
  const runtimeHost = window.location.hostname;
  if (runtimeHost.endsWith(".replit.app")) {
    return { host: runtimeHost, isProd: true };
  }
  // Otherwise fall back to the build-time domain list (prefers prod over dev)
  const domains = (typeof __REPLIT_DOMAINS__ !== "undefined" ? __REPLIT_DOMAINS__ : "")
    .split(",").map((d) => d.trim()).filter(Boolean);
  const prod = domains.find((d) => d.endsWith(".replit.app"));
  if (prod) return { host: prod, isProd: true };
  return { host: domains[0] ?? runtimeHost, isProd: false };
}

const TOOLS = [
  {
    name: "get_ldong_code",
    operation: "ldongCode",
    desc: "Look up legal administrative district codes (provinces and cities) — required before region-based searches.",
  },
  {
    name: "get_area_based_list",
    operation: "areaBasedList",
    desc: "List medical tourism facilities filtered by province or city/county.",
  },
  {
    name: "get_location_based_list",
    operation: "locationBasedList",
    desc: "Find facilities within a GPS radius (up to 20 km) using WGS84 coordinates.",
  },
  {
    name: "search_medical_by_keyword",
    operation: "searchKeyword",
    desc: "Search facilities by keyword across all regions.",
  },
  {
    name: "get_medical_sync_list",
    operation: "mdclTursmSyncList",
    desc: "Retrieve the full sync list with display status and legacy content ID mapping.",
  },
  {
    name: "get_detail_common",
    operation: "detailCommon",
    desc: "Fetch common details — title, address, GPS coordinates, phone, homepage, and overview text.",
  },
  {
    name: "get_detail_intro",
    operation: "detailIntro",
    desc: "Fetch introductory facility details — opening hours, rest days, parking, capacity, age suitability.",
  },
  {
    name: "get_detail_medical",
    operation: "detailMdclTursm",
    desc: "Fetch medical-specific details — specialties, languages served, reservation status, SNS info.",
  },
];

const LANG_CODES = [
  { code: "ENG", lang: "English" },
  { code: "JPN", lang: "Japanese" },
  { code: "CHS", lang: "Simplified Chinese" },
  { code: "RUS", lang: "Russian" },
];

const MANUS_INSTRUCTIONS = `# Manus AI Instructions — visitkorea-medicaltourism-mcp

## What this MCP does

This server exposes **8 tools** that provide structured access to Korea's official **Medical Tourism (의료관광)** dataset. The underlying data is curated by the **Korea Tourism Organization (KTO)** and published as an Open API on [data.go.kr](https://www.data.go.kr/data/15143913/openapi.do) — Korea's Public Data Portal — under the service name \`MdclTursmService\`. It covers KTO-certified medical tourism facilities across South Korea, including hospitals, specialist clinics, and wellness centres, with multilingual support for 4 international languages. Tools are called over **Streamable HTTP** (\`/mcp\`).

## When to use this MCP

Activate this MCP when a user asks about:

- Medical tourism in South Korea — finding hospitals, clinics, or certified medical facilities
- Searching for facilities by region, GPS location, or keyword (e.g. "dermatology clinics in Seoul", "English-speaking hospital near Gangnam")
- Getting structured details about a specific facility — address, phone, homepage, specialties, languages served, opening hours, or reservation status
- Building or refreshing a local database of Korean medical tourism facilities (use the sync list tool)
- Any query where the user is a foreign visitor to South Korea seeking medical services

## Tool Usage Guide

### Step 1 — Retrieve district codes (region-based searches only)

Before calling any area-based search, call \`get_ldong_code\` to look up the correct province/city code (\`l_dong_regn_cd\`) and optionally the district code (\`l_dong_signgu_cd\`).

**Skip this step** if the user is searching by keyword or GPS coordinates.

### Step 2 — Choose the right search tool

| User scenario | Tool to call |
|---------------|--------------|
| User specifies a region (e.g. Seoul, Busan) | \`get_area_based_list\` |
| User gives a location or asks "near me" | \`get_location_based_list\` |
| User provides a keyword or facility name | \`search_medical_by_keyword\` |
| Building or syncing a complete local database | \`get_medical_sync_list\` |

### Step 3 — Fetch details for specific facilities

Once you have a \`content_id\` from a list result, use the three detail tools:

| Tool | What it returns |
|------|-----------------|
| \`get_detail_common\` | Name, address, GPS coordinates, phone, homepage, overview text |
| \`get_detail_intro\` | Opening hours, rest days, parking, capacity, age suitability |
| \`get_detail_medical\` | Medical specialties, languages served, reservation status, SNS links |

Always call \`get_detail_common\` first. Call \`get_detail_medical\` when the user needs specialty or language information.

## Language parameter

All tools accept an optional \`lang_div_cd\` parameter. Set it based on the user's language:

| Code | Language |
|------|----------|
| \`ENG\` | English |
| \`JPN\` | Japanese (日本語) |
| \`CHS\` | Simplified Chinese (简体中文) |
| \`RUS\` | Russian (Русский) |

If not specified, the API returns Korean (\`KOR\`) field labels. For international users, always pass the appropriate code.

## Important notes

- \`get_ldong_code\` is **required** before \`get_area_based_list\` unless the user already provides a known region code.
- \`get_location_based_list\` requires WGS84 GPS coordinates (\`map_x\` = longitude, \`map_y\` = latitude) and a radius in metres (maximum 20,000 m).
- \`get_detail_medical\` is specific to this medical tourism dataset — it returns fields such as medical specialties (\`sickDivNm\`), foreign language support (\`foreignLangCd\`), and reservation status that do not appear in other detail endpoints.
- Results are paginated; use \`num_of_rows\` and \`page_no\` to page through large result sets.
- The dataset is refreshed once daily. All data reflects the most recent KTO-approved records from the 공공데이터포털 open API platform.

## Example workflow

**User asks:** "Find English-speaking dermatology clinics in Seoul"

1. Call \`get_ldong_code\` with \`l_dong_regn_cd=11\` (Seoul) to confirm available district codes.
2. Call \`get_area_based_list\` with \`l_dong_regn_cd=11\` and \`lang_div_cd=ENG\` to retrieve facilities in the Seoul region.
3. For each result with a \`content_id\`, call \`get_detail_medical\` to check \`foreignLangCd\` for English and \`sickDivNm\` for dermatology.
4. Also call \`get_detail_common\` to retrieve the address, phone number, and homepage URL.
5. Return a structured list of matching facilities with name, address, phone, specialties, and language support clearly presented.
`;

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="text-xs px-2 py-1 rounded bg-white/10 hover:bg-white/20 transition-colors font-mono border border-white/20"
    >
      {copied ? "Copied!" : "Copy"}
    </button>
  );
}

function ManusInstructions() {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await navigator.clipboard.writeText(MANUS_INSTRUCTIONS);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className="flex items-stretch gap-2">
        <CollapsibleTrigger className="flex-1 flex items-center gap-2 px-5 py-3.5 bg-white border border-border rounded-xl hover:bg-muted/50 transition-colors text-left">
          <span
            className="text-muted-foreground text-xs transition-transform duration-200 select-none"
            style={{ transform: open ? "rotate(90deg)" : "rotate(0deg)" }}
          >
            ▶
          </span>
          <span className="text-sm font-semibold text-foreground">Manus AI Instructions</span>
          <span className="text-xs text-muted-foreground">
            How and when to use this MCP — click to expand
          </span>
        </CollapsibleTrigger>
        <button
          onClick={handleCopy}
          className="text-xs px-3 py-1 rounded-xl border border-border bg-white hover:bg-muted/50 transition-colors font-mono text-muted-foreground shrink-0"
        >
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <CollapsibleContent>
        <div className="mt-1 rounded-xl border border-border bg-white px-6 py-6 prose prose-sm max-w-none
          prose-headings:font-semibold prose-headings:text-foreground
          prose-h1:text-lg prose-h2:text-base prose-h3:text-sm
          prose-p:text-muted-foreground prose-p:leading-relaxed
          prose-li:text-muted-foreground
          prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-xs prose-code:font-mono prose-code:text-foreground prose-code:before:content-none prose-code:after:content-none
          prose-table:text-sm prose-th:text-foreground prose-th:font-semibold prose-td:text-muted-foreground
          prose-strong:text-foreground
          prose-a:text-primary">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{MANUS_INSTRUCTIONS}</ReactMarkdown>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

const { host: publicHost, isProd } = getDomainInfo();

const CONNECTOR_JSON = `{
  "mcpServers": {
    "visitkorea-medicaltourism": {
      "url": "https://${publicHost}/mcp"
    }
  }
}`;

export default function App() {
  return (
    <div className="min-h-screen bg-[hsl(220,20%,97%)]">
      {/* Header */}
      <header className="border-b border-border bg-white">
        <div className="max-w-4xl mx-auto px-6 py-5 flex items-center gap-3">
          <span className="text-2xl">🇰🇷</span>
          <div>
            <h1 className="text-lg font-semibold text-foreground leading-tight">
              visitkorea-medicaltourism-mcp
            </h1>
            <p className="text-xs text-muted-foreground">
              Korea Tourism Organization (KTO) · Open API via data.go.kr · MCP Server
            </p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full bg-green-50 text-green-700 border border-green-200">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              Live · Streamable HTTP
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-10 space-y-10">

        {/* Hero */}
        <section>
          <h2 className="text-2xl font-bold text-foreground">
            AI-ready access to Korea's medical tourism data
          </h2>
          <p className="mt-2 text-muted-foreground max-w-2xl">
            This MCP (Model Context Protocol) server wraps the{" "}
            <code className="text-xs bg-muted px-1 py-0.5 rounded">MdclTursmService</code> Open API
            published on <strong className="text-foreground">data.go.kr</strong> (Korea's Public Data Portal),
            based on medical tourism data curated by the{" "}
            <strong className="text-foreground">Korea Tourism Organization (KTO)</strong>.
            It exposes 8 structured tools that Manus AI, Claude, and other MCP-compatible agents can
            call directly via Streamable HTTP.
          </p>
        </section>

        {/* Connector JSON */}
        <section>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-3">
            Connect your AI agent
          </h3>

          {/* Manus AI callout */}
          <div className="mb-4 rounded-xl border border-blue-200 bg-blue-50 px-5 py-4">
            <p className="text-sm font-semibold text-blue-800 mb-2">Connecting from Manus AI</p>
            <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
              <li>Open <strong>Settings → Connectors → Add Connectors → Custom MCP</strong> in Manus AI.</li>
              <li>Click <strong>Import by JSON</strong> and paste the connector JSON below, or enter the URL directly.</li>
            </ol>
            <div className="mt-3 flex items-center gap-2 rounded-lg bg-blue-100 border border-blue-200 px-3 py-2">
              <code className="text-xs font-mono text-blue-900 flex-1 break-all">
                https://{publicHost}/mcp
              </code>
              <CopyButton text={`https://${publicHost}/mcp`} />
            </div>
          </div>

          {/* JSON config */}
          <div className="rounded-xl bg-slate-900 text-slate-100 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/10">
              <span className="text-xs font-medium text-slate-400">MCP Connector JSON (other clients)</span>
              <CopyButton text={CONNECTOR_JSON} />
            </div>
            <pre className="px-4 py-4 text-sm font-mono overflow-x-auto leading-relaxed">
              <code>{CONNECTOR_JSON}</code>
            </pre>
          </div>
          {!isProd && (
            <p className="mt-2 text-xs text-amber-600 dark:text-amber-400">
              This is the development URL. Deploy the project to get your permanent{" "}
              <code className="bg-muted px-1 py-0.5 rounded">.replit.app</code> production URL.
            </p>
          )}
        </section>

        {/* Tools */}
        <section>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-3">
            Available Tools ({TOOLS.length})
          </h3>
          <div className="grid gap-3">
            {TOOLS.map((tool, i) => (
              <div
                key={tool.name}
                className="bg-white border border-border rounded-xl px-5 py-4 flex gap-4 items-start"
              >
                <span className="mt-0.5 text-xs font-mono font-bold text-muted-foreground bg-muted rounded px-1.5 py-0.5 shrink-0">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <code className="text-sm font-mono font-semibold text-primary">
                      {tool.name}
                    </code>
                    <span className="text-xs text-muted-foreground font-mono bg-muted px-1.5 py-0.5 rounded">
                      {tool.operation}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">{tool.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Language codes */}
        <section>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-3">
            Supported Languages
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {LANG_CODES.map(({ code, lang }) => (
              <div
                key={code}
                className="bg-white border border-border rounded-xl px-4 py-3 text-center"
              >
                <code className="text-base font-mono font-bold text-primary">{code}</code>
                <p className="mt-0.5 text-xs text-muted-foreground">{lang}</p>
              </div>
            ))}
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Pass one of these as the <code className="bg-muted px-1 py-0.5 rounded">lang_div_cd</code> parameter in every tool call.
          </p>
        </section>

        {/* Meta cards — 4-column grid */}
        <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-white border border-border rounded-xl px-5 py-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Data Owner</p>
            <p className="text-sm font-medium">Korea Tourism Organization</p>
            <p className="text-xs text-muted-foreground mt-0.5">KTO (한국관광공사)</p>
          </div>
          <div className="bg-white border border-border rounded-xl px-5 py-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">API Provider</p>
            <p className="text-sm font-medium">data.go.kr</p>
            <p className="text-xs text-muted-foreground mt-0.5">Korea Public Data Portal</p>
          </div>
          <div className="bg-white border border-border rounded-xl px-5 py-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Refresh Cycle</p>
            <p className="text-sm font-medium">Once daily</p>
            <p className="text-xs text-muted-foreground mt-0.5">1,000 requests / day (dev)</p>
          </div>
          <div className="bg-white border border-border rounded-xl px-5 py-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Transport</p>
            <p className="text-sm font-medium">Streamable HTTP</p>
            <p className="text-xs text-muted-foreground mt-0.5">MCP protocol compatible</p>
          </div>
        </section>

        {/* Manus AI Instructions — collapsible */}
        <section>
          <ManusInstructions />
        </section>

        {/* Footer links */}
        <section className="text-center py-4 border-t border-border">
          <a
            href="https://www.data.go.kr/data/15143913/openapi.do"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-primary hover:underline"
          >
            data.go.kr API Reference →
          </a>
          <span className="mx-3 text-muted-foreground">·</span>
          <a
            href="https://github.com/leejaew/visitkorea-medicaltourism-mcp"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-primary hover:underline"
          >
            GitHub →
          </a>
        </section>

      </main>
    </div>
  );
}
