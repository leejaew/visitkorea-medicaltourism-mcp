import { useState } from "react";

declare const __REPLIT_DOMAINS__: string;

function getDomainInfo(): { host: string; isProd: boolean } {
  const domains = __REPLIT_DOMAINS__;
  if (domains) {
    const list = domains.split(",").map((d) => d.trim()).filter(Boolean);
    const prod = list.find((d) => d.endsWith(".replit.app"));
    if (prod) return { host: prod, isProd: true };
    return { host: list[0] ?? window.location.hostname, isProd: false };
  }
  return { host: window.location.hostname, isProd: false };
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

const { host: publicHost, isProd } = getDomainInfo();

const CONNECTOR_JSON = `{
  "mcpServers": {
    "visitkorea-medicaltourism": {
      "url": "https://${publicHost}/sse",
      "type": "sse"
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
              Korea Tourism Organization · Medical Tourism Information API · MCP Server
            </p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full bg-green-50 text-green-700 border border-green-200">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              Live · SSE
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
            This MCP (Model Context Protocol) server wraps the official Korea Tourism Organization{" "}
            <code className="text-xs bg-muted px-1 py-0.5 rounded">MdclTursmService</code> API,
            exposing 8 structured tools that Manus AI, Claude, and other MCP-compatible agents can
            call directly via Server-Sent Events (SSE).
          </p>
        </section>

        {/* Connector JSON */}
        <section>
          <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-3">
            Connect your AI agent
          </h3>
          <div className="rounded-xl bg-slate-900 text-slate-100 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/10">
              <span className="text-xs font-medium text-slate-400">MCP Connector JSON</span>
              <CopyButton text={CONNECTOR_JSON} />
            </div>
            <pre className="px-4 py-4 text-sm font-mono overflow-x-auto leading-relaxed">
              <code>{CONNECTOR_JSON}</code>
            </pre>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Paste this into your AI agent's custom connector settings. The SSE endpoint is at{" "}
            <code className="bg-muted px-1 py-0.5 rounded">
              https://{publicHost}/sse
            </code>
          </p>
          {!isProd && (
            <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
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

        {/* API info */}
        <section className="grid sm:grid-cols-3 gap-4">
          <div className="bg-white border border-border rounded-xl px-5 py-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Data Source</p>
            <p className="text-sm font-medium">Korea Tourism Organization</p>
            <p className="text-xs text-muted-foreground mt-0.5">MdclTursmService</p>
          </div>
          <div className="bg-white border border-border rounded-xl px-5 py-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Refresh Cycle</p>
            <p className="text-sm font-medium">Once daily</p>
            <p className="text-xs text-muted-foreground mt-0.5">1,000 requests / day (dev)</p>
          </div>
          <div className="bg-white border border-border rounded-xl px-5 py-4">
            <p className="text-xs text-muted-foreground uppercase tracking-wider font-semibold mb-1">Transport</p>
            <p className="text-sm font-medium">SSE (Server-Sent Events)</p>
            <p className="text-xs text-muted-foreground mt-0.5">MCP protocol compatible</p>
          </div>
        </section>

        {/* API reference link */}
        <section className="text-center py-4 border-t border-border">
          <a
            href="https://www.data.go.kr/data/15143913/openapi.do"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-primary hover:underline"
          >
            Official API Reference →
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
