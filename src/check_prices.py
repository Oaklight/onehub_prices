"""Price diff checker: fetches official pricing pages and diffs against local YAML files."""

import fnmatch
import os
import re
import sys

from _vendor import httpclient
from _vendor import yaml

# Resolve project root relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

URLS_FILE = os.path.join(PROJECT_ROOT, "llm_readable_pricing_urls.yaml")
MANUAL_PRICES_DIR = os.path.join(PROJECT_ROOT, "manual_prices")

# Mapping from llm_readable_pricing_urls.yaml provider key to YAML filename
PROVIDER_YAML_MAP = {
    "OpenAI": "OpenAI.yaml",
    "Anthropic": "Anthropic.yaml",
    "Aliyun (阿里云百炼)": "阿里云百炼.yaml",
    "MiniMax": "MiniMax.yaml",
    "xAI": "xAI.yaml",
}

# Mapping from llm_readable_pricing_urls.yaml provider key to parser function name
PROVIDER_PARSER_MAP = {
    "OpenAI": "parse_openai",
    "Anthropic": "parse_anthropic",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


# ---------------------------------------------------------------------------
# Fetcher
# ---------------------------------------------------------------------------


def load_provider_urls():
    """Load provider pricing URLs from llm_readable_pricing_urls.yaml."""
    with open(URLS_FILE, "r", encoding="utf-8") as f:
        data = yaml.load(f)
    return data.get("providers", {})


def fetch_pricing_md(url):
    """Fetch markdown content from a pricing URL."""
    resp = httpclient.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


# ---------------------------------------------------------------------------
# Parsers — each returns list of dicts with unified schema:
#   { "model": str, "input": str|None, "output": str|None,
#     "cached_tokens": str|None, ... extra fields }
# Price strings use the format "X usd / M" or "0" or None (not listed).
# ---------------------------------------------------------------------------


def _extract_bracket_content(text, start_pos):
    """Extract content between balanced brackets starting at start_pos.

    Args:
        text: source text
        start_pos: position of the opening bracket '['

    Returns:
        The content between the outermost brackets, or None if unbalanced.
    """
    if text[start_pos] != "[":
        return None
    depth = 0
    for i in range(start_pos, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                return text[start_pos + 1 : i]
    return None


def _fmt_price(value, unit="usd / M"):
    """Format a numeric price value into a price string."""
    if value is None or value == "" or value == "-":
        return None
    if isinstance(value, str):
        if value.lower() == "free":
            return "0"
        return None
    if value == 0:
        return "0"
    # Remove trailing zeros for clean display
    s = f"{value:g}"
    return f"{s} {unit}"


def parse_openai(md_text):
    """Parse OpenAI pricing.md JSX rows into unified price list.

    Extracts data from two sources:
    1. The first standard-tier TextTokenPricingTables rows={[...]} block (flagship models)
    2. The specialized models GroupedPricingTable rows (deep research, embedding, etc.)
    """
    results = []

    # --- 1. Flagship models: first standard-tier rows={[...]} block ---
    # Find the first <div data-content-switcher-pane data-value="standard"> block
    # and extract its rows={[...]}
    standard_pane_pattern = re.compile(
        r'data-content-switcher-pane\s+data-value="standard".*?'
        r"rows=\{\[(.*?)\]\}",
        re.DOTALL,
    )
    match = standard_pane_pattern.search(md_text)
    if match:
        rows_text = match.group(1)
        _parse_jsx_rows(rows_text, results)

    # --- 2. Specialized models (deep research, computer use, embedding, moderation) ---
    # These use { model: "Category", rows: [...] } format
    # We need bracket-counting since inner arrays contain ']' characters
    spec_start = md_text.find("Specialized models")
    if spec_start != -1:
        spec_text = md_text[spec_start:]
        model_header_pattern = re.compile(r'model:\s*"([^"]+)",\s*rows:\s*\[')
        for m in model_header_pattern.finditer(spec_text):
            category = m.group(1)
            if category in ("Containers", "File search", "Agent Kit"):
                continue
            # Extract balanced bracket content starting after "rows: ["
            bracket_start = m.end() - 1  # position of '['
            rows_text = _extract_bracket_content(spec_text, bracket_start)
            if rows_text:
                _parse_jsx_rows(rows_text, results)

    return results


def _parse_jsx_rows(rows_text, results):
    """Parse JSX row arrays like ["model-name", input, cached, output] into results list."""
    # Match each row: ["model-name", value, value, value]
    row_pattern = re.compile(
        r'\["([^"]+)"\s*,\s*'  # model name
        r"([^,\]]+)\s*,\s*"  # input
        r"([^,\]]+)\s*,\s*"  # cached
        r"([^\]]+)\]"  # output
    )
    for row_match in row_pattern.finditer(rows_text):
        model_name = row_match.group(1).strip()
        input_val = row_match.group(2).strip()
        cached_val = row_match.group(3).strip()
        output_val = row_match.group(4).strip()

        # Clean up model name: remove context annotations like "(<272K context length)"
        model_name = re.sub(r"\s*\([^)]*\)\s*$", "", model_name).strip()

        entry = {
            "model": model_name,
            "input": _parse_jsx_value(input_val),
            "output": _parse_jsx_value(output_val),
        }
        cached = _parse_jsx_value(cached_val)
        if cached is not None:
            entry["cached_tokens"] = cached

        results.append(entry)


def _parse_jsx_value(val_str):
    """Parse a single JSX price value into a price string."""
    val_str = val_str.strip().strip('"').strip("'")
    if val_str in ("null", '""', "''", '"-"', "-"):
        return None
    if val_str.lower() == '"free"' or val_str.lower() == "free":
        return "0"
    try:
        num = float(val_str)
        if num == 0:
            return "0"
        return _fmt_price(num)
    except ValueError:
        return None


def parse_anthropic(md_text):
    """Parse Anthropic pricing.md markdown table into unified price list.

    Expected table format:
    | Model | Base Input Tokens | 5m Cache Writes | 1h Cache Writes | Cache Hits & Refreshes | Output Tokens |
    | Claude Opus 4.6 | $5 / MTok | ... | ... | $0.50 / MTok | $25 / MTok |
    """
    results = []

    # Model name to API model ID mapping
    # Display name -> YAML canonical model ID
    # NOTE: When Anthropic adds new models, add a mapping here.
    name_to_id = {
        "Claude Opus 4.6": "claude-opus-4-6",
        "Claude Opus 4.5": "claude-opus-4-5",
        "Claude Opus 4.1": "claude-opus-4-1",
        "Claude Opus 4": "claude-opus-4",
        "Claude Sonnet 4.6": "claude-sonnet-4-6",
        "Claude Sonnet 4.5": "claude-sonnet-4-5",
        "Claude Sonnet 4": "claude-sonnet-4",
        "Claude Sonnet 3.7": "claude-3-7-sonnet",
        "Claude Sonnet 3.5 v2": "claude-3-5-sonnet-v2",
        "Claude Sonnet 3.5": "claude-3-5-sonnet",
        "Claude Haiku 4.5": "claude-haiku-4-5",
        "Claude Haiku 3.5": "claude-3-5-haiku",
        "Claude Opus 3": "claude-3-opus",
        "Claude Haiku 3": "claude-3-haiku",
    }

    # Find the main pricing table
    lines = md_text.split("\n")
    in_table = False
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            if in_table:
                break
            continue
        cells = [c.strip() for c in line.split("|")]
        # Remove empty first/last cells from leading/trailing pipes
        cells = [c for c in cells if c]

        # Skip header and separator rows
        if "Model" in cells[0] or cells[0].startswith("---"):
            in_table = True
            continue
        if not in_table:
            continue

        if len(cells) < 6:
            continue

        model_display = cells[0]
        base_input = cells[1]
        cache_hits = cells[4]
        output = cells[5]

        # Clean model name: remove markdown links like ([deprecated](/docs/...))
        # Strip everything from first " (" onwards
        paren_idx = model_display.find(" (")
        model_clean = (
            model_display[:paren_idx].strip()
            if paren_idx != -1
            else model_display.strip()
        )

        model_id = name_to_id.get(model_clean)
        if not model_id:
            continue

        entry = {
            "model": model_id,
            "input": _parse_anthropic_price(base_input),
            "output": _parse_anthropic_price(output),
        }
        cached = _parse_anthropic_price(cache_hits)
        if cached is not None:
            entry["cached_tokens"] = cached

        results.append(entry)

    return results


def _parse_anthropic_price(price_str):
    """Parse Anthropic price string like '$5 / MTok' into 'X usd / M'."""
    price_str = price_str.strip()
    if not price_str or price_str == "-":
        return None

    # Match pattern: $X.XX / MTok
    m = re.match(r"\$?([\d.]+)\s*/\s*MTok", price_str)
    if m:
        val = float(m.group(1))
        return _fmt_price(val)
    return None


# ---------------------------------------------------------------------------
# YAML Loader + Alias Resolver
# ---------------------------------------------------------------------------


def load_yaml_prices(provider_yaml_file):
    """Load pricing data from a single provider YAML file.

    Returns:
        dict: { model_name: { "input": str, "output": str, "aliases": list, "extra_ratios": dict } }
    """
    file_path = os.path.join(MANUAL_PRICES_DIR, provider_yaml_file)
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.load(f)

    if not data or "models" not in data:
        return {}

    # Get the first (and usually only) provider key
    for provider_name, models in data["models"].items():
        if models:
            return models
    return {}


def build_alias_index(yaml_models):
    """Build a mapping from all known names (including aliases) to canonical model name.

    Returns:
        tuple: (name_to_canonical dict, wildcard_patterns list of (pattern, canonical))
    """
    name_to_canonical = {}
    wildcard_patterns = []

    for model_name, model_info in yaml_models.items():
        if model_info is None:
            continue
        name_to_canonical[model_name] = model_name

        aliases = model_info.get("aliases", [])
        if isinstance(aliases, str):
            aliases = [a.strip() for a in aliases.split(",")]

        for alias in aliases:
            alias = alias.strip()
            if "*" in alias:
                wildcard_patterns.append((alias, model_name))
            else:
                name_to_canonical[alias] = model_name

    return name_to_canonical, wildcard_patterns


def resolve_model_name(name, name_to_canonical, wildcard_patterns):
    """Resolve an official model name to the canonical YAML model name."""
    if name in name_to_canonical:
        return name_to_canonical[name]

    # Try wildcard matching
    for pattern, canonical in wildcard_patterns:
        if fnmatch.fnmatch(name, pattern):
            return canonical

    return None


# ---------------------------------------------------------------------------
# Price comparison
# ---------------------------------------------------------------------------


def normalize_price(price_str):
    """Normalize a price string for comparison.

    Returns (float_value, unit) or None if not parseable.
    """
    if price_str is None:
        return None
    price_str = str(price_str).strip()
    if price_str == "0":
        return (0.0, "")

    # Try to parse as "X unit" format
    m = re.match(r"^([\d.]+)\s*(.*)$", price_str.strip())
    if m:
        return (float(m.group(1)), m.group(2).strip())
    return None


def prices_equal(a, b):
    """Compare two price strings for equality."""
    na = normalize_price(a)
    nb = normalize_price(b)

    if na is None and nb is None:
        return True
    if na is None or nb is None:
        return False

    # Compare numeric values with small tolerance
    return abs(na[0] - nb[0]) < 0.0001


def get_yaml_price_str(model_info, field):
    """Extract a price string from YAML model info for a given field.

    For top-level fields (input, output): return the value directly.
    For extra_ratios fields (cached_tokens, etc.): find in extra_ratios list.
    """
    if model_info is None:
        return None

    if field in ("input", "output"):
        val = model_info.get(field)
        if val is None:
            return None
        return str(val)

    # Look in extra_ratios
    extra_ratios = model_info.get("extra_ratios", [])
    if not extra_ratios:
        return None
    for item in extra_ratios:
        if isinstance(item, dict) and field in item:
            return str(item[field])
    return None


# ---------------------------------------------------------------------------
# Diff Engine
# ---------------------------------------------------------------------------


def diff_prices(official_prices, yaml_models):
    """Compare official prices against YAML data.

    Args:
        official_prices: list of dicts from parser
        yaml_models: dict from YAML loader

    Returns:
        dict with keys: matched, price_changed, new_models, yaml_only
    """
    name_to_canonical, wildcard_patterns = build_alias_index(yaml_models)

    matched = []
    price_changed = []
    new_models = []
    seen_canonical = set()

    for entry in official_prices:
        official_model = entry["model"]
        canonical = resolve_model_name(
            official_model, name_to_canonical, wildcard_patterns
        )

        if canonical is None:
            new_models.append(entry)
            continue

        seen_canonical.add(canonical)
        yaml_info = yaml_models.get(canonical)

        # Compare each price field
        diffs = []
        for field in ("input", "output", "cached_tokens"):
            official_val = entry.get(field)
            yaml_val = get_yaml_price_str(yaml_info, field)

            if official_val is None:
                continue

            if not prices_equal(official_val, yaml_val):
                diffs.append(
                    {
                        "field": field,
                        "official": official_val,
                        "yaml": yaml_val,
                    }
                )

        if diffs:
            price_changed.append(
                {
                    "official_name": official_model,
                    "canonical_name": canonical,
                    "diffs": diffs,
                }
            )
        else:
            matched.append(
                {"official_name": official_model, "canonical_name": canonical}
            )

    # Find YAML-only models (not seen in official data)
    yaml_only = []
    for model_name in yaml_models:
        if model_name not in seen_canonical:
            yaml_only.append(model_name)

    return {
        "matched": matched,
        "price_changed": price_changed,
        "new_models": new_models,
        "yaml_only": yaml_only,
    }


# ---------------------------------------------------------------------------
# Report Formatter
# ---------------------------------------------------------------------------


def print_report(provider_name, diff_result):
    """Print a formatted diff report for a provider."""
    matched = diff_result["matched"]
    changed = diff_result["price_changed"]
    new = diff_result["new_models"]
    yaml_only = diff_result["yaml_only"]

    print(f"\n{'=' * 60}")
    print(f"  {provider_name} Price Diff Report")
    print(f"{'=' * 60}")

    # Summary
    print(
        f"\n  MATCH: {len(matched)}  |  CHANGED: {len(changed)}  "
        f"|  NEW: {len(new)}  |  YAML_ONLY: {len(yaml_only)}"
    )

    # Price changes
    if changed:
        print(f"\n--- PRICE_CHANGED ({len(changed)}) ---")
        for item in changed:
            print(
                f"\n  {item['official_name']}"
                + (
                    f" -> {item['canonical_name']}"
                    if item["official_name"] != item["canonical_name"]
                    else ""
                )
            )
            for d in item["diffs"]:
                print(
                    f"    {d['field']:20s}  official: {d['official']!s:20s}  "
                    f"yaml: {d['yaml']!s}"
                )

    # New models
    if new:
        print(f"\n--- NEW_MODEL ({len(new)}) ---")
        for item in new:
            parts = [f"  {item['model']}:"]
            if item.get("input"):
                parts.append(f"input={item['input']}")
            if item.get("output"):
                parts.append(f"output={item['output']}")
            if item.get("cached_tokens"):
                parts.append(f"cached={item['cached_tokens']}")
            print("  ".join(parts))

    # YAML-only models
    if yaml_only:
        print(f"\n--- YAML_ONLY ({len(yaml_only)}) ---")
        print("  (Models in YAML but not found in official pricing page)")
        for name in yaml_only:
            print(f"  {name}")

    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_provider(provider_key, provider_info):
    """Run price check for a single provider."""
    pricing_url = provider_info.get("pricing_md")
    if not pricing_url:
        print(f"[SKIP] {provider_key}: no pricing_md URL")
        return None

    # Get parser
    parser_name = PROVIDER_PARSER_MAP.get(provider_key)
    if not parser_name:
        print(f"[SKIP] {provider_key}: no parser implemented")
        return None

    parser_fn = globals().get(parser_name)
    if not parser_fn:
        print(f"[SKIP] {provider_key}: parser function {parser_name} not found")
        return None

    # Get YAML file
    yaml_file = PROVIDER_YAML_MAP.get(provider_key)
    if not yaml_file:
        print(f"[SKIP] {provider_key}: no YAML file mapping")
        return None

    yaml_path = os.path.join(MANUAL_PRICES_DIR, yaml_file)
    if not os.path.exists(yaml_path):
        print(f"[SKIP] {provider_key}: YAML file {yaml_file} not found")
        return None

    # Fetch official prices
    print(f"[FETCH] {provider_key}: {pricing_url}")
    try:
        md_text = fetch_pricing_md(pricing_url)
    except httpclient.HttpClientError as e:
        print(f"[ERROR] {provider_key}: failed to fetch pricing page: {e}")
        return None

    # Parse official prices
    official_prices = parser_fn(md_text)
    if not official_prices:
        print(f"[WARN] {provider_key}: parser returned no results")
        return None

    print(
        f"[PARSE] {provider_key}: {len(official_prices)} models parsed from official page"
    )

    # Load YAML prices
    yaml_models = load_yaml_prices(yaml_file)
    print(f"[YAML]  {provider_key}: {len(yaml_models)} models in YAML")

    # Diff
    result = diff_prices(official_prices, yaml_models)
    print_report(provider_key, result)
    return result


def main():
    provider_urls = load_provider_urls()

    # Determine which providers to check
    if len(sys.argv) > 1:
        requested = sys.argv[1:]
        # Match by key or partial key
        providers_to_check = {}
        for req in requested:
            for key, info in provider_urls.items():
                if req.lower() in key.lower():
                    providers_to_check[key] = info
                    break
            else:
                print(f"[WARN] Provider not found: {req}")
    else:
        providers_to_check = {
            k: v
            for k, v in provider_urls.items()
            if v.get("pricing_md") and k in PROVIDER_PARSER_MAP
        }

    if not providers_to_check:
        print("No providers to check.")
        return

    has_price_changes = False
    for provider_key, provider_info in providers_to_check.items():
        result = check_provider(provider_key, provider_info)
        if result and result["price_changed"]:
            has_price_changes = True

    # Exit 1 only for actual price discrepancies, not for new/missing models
    sys.exit(1 if has_price_changes else 0)


if __name__ == "__main__":
    main()
