import os
import re
import sys


def load_env_file(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip()
            if k and v:
                os.environ.setdefault(k, v)


def parse_markdown_value(md: str, label: str) -> str | None:
    # Find the line after the label line
    # Example structure: "Service Bus namespace" newline then the value on the next line
    pattern = re.compile(rf"^{re.escape(label)}\s*:?$", re.IGNORECASE | re.MULTILINE)
    m = pattern.search(md)
    if not m:
        return None
    # Take next non-empty line after match
    after = md[m.end() :]
    for ln in after.splitlines():
        ln = ln.strip()
        if ln:
            return ln
    return None


def parse_markdown_block(
    md: str, start_label: str, stop_labels: list[str]
) -> str | None:
    # Capture possibly wrapped values (e.g., secrets broken across lines)
    pattern = re.compile(
        rf"^{re.escape(start_label)}\s*:?$", re.IGNORECASE | re.MULTILINE
    )
    m = pattern.search(md)
    if not m:
        return None
    after = md[m.end() :]
    buf: list[str] = []
    for ln in after.splitlines():
        raw = ln.rstrip("\n")
        if not raw.strip():
            continue
        # Stop if we hit another label
        stop = False
        for lab in stop_labels:
            if re.match(rf"^{re.escape(lab)}\b", raw.strip(), re.IGNORECASE):
                stop = True
                break
        if stop:
            break
        buf.append(raw.strip())
        # Truncate to a reasonable length to avoid slurping the whole doc
        if sum(len(x) for x in buf) > 256:
            break
    return "".join(buf) if buf else None


def ensure_iris_env():
    # Map any AZURE_* to IRIS_* if present
    if os.getenv("AZURE_CLIENT_ID") and not os.getenv("IRIS_CLIENT_ID"):
        os.environ["IRIS_CLIENT_ID"] = os.environ["AZURE_CLIENT_ID"]
    if os.getenv("AZURE_TENANT_ID") and not os.getenv("IRIS_TENANT_ID"):
        os.environ["IRIS_TENANT_ID"] = os.environ["AZURE_TENANT_ID"]
    if os.getenv("AZURE_CLIENT_SECRET") and not os.getenv("IRIS_CLIENT_SECRET"):
        os.environ["IRIS_CLIENT_SECRET"] = os.environ["AZURE_CLIENT_SECRET"]

    # Parse markdown for namespace and queue name if not set
    md_path = os.path.join(os.getcwd(), "elexon_api_IRIS.md")
    if os.path.exists(md_path):
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                md = f.read()
            # Try to recover Client ID and Secret if not provided in env files
            if not os.getenv("IRIS_CLIENT_ID"):
                cid = parse_markdown_block(
                    md,
                    start_label="Client ID",
                    stop_labels=[
                        "Service Bus namespace",
                        "Tenant ID",
                        "Default queue",
                        "Queue name",
                        "Queue URL",
                        "Client secret",
                    ],
                )
                if not cid:
                    # Some docs may contain "nt ID" due to formatting issues
                    cid = parse_markdown_block(
                        md,
                        start_label="Client secret:",
                        stop_labels=[
                            "Client ID",
                            "Service Bus namespace",
                            "Tenant ID",
                            "Default queue",
                            "Queue name",
                            "Queue URL",
                        ],
                    )
                if cid:
                    os.environ["IRIS_CLIENT_ID"] = cid
            if not os.getenv("IRIS_CLIENT_SECRET"):
                sec = parse_markdown_block(
                    md,
                    start_label="Client secret",
                    stop_labels=[
                        "Client ID",
                        "Service Bus namespace",
                        "Tenant ID",
                        "Default queue",
                        "Queue name",
                        "Queue URL",
                    ],
                )
                if sec:
                    os.environ["IRIS_CLIENT_SECRET"] = sec
            if not os.getenv("IRIS_SERVICEBUS_NAMESPACE"):
                ns = parse_markdown_value(md, "Service Bus namespace")
                if ns:
                    os.environ["IRIS_SERVICEBUS_NAMESPACE"] = ns
            if not os.getenv("IRIS_QUEUE_NAME"):
                qn = parse_markdown_value(md, "Queue name")
                if qn:
                    os.environ["IRIS_QUEUE_NAME"] = qn
        except Exception:
            pass

    # Default BQ project if not provided
    os.environ.setdefault("BQ_PROJECT", "jibber-jabber-knowledge")

    required = [
        "IRIS_TENANT_ID",
        "IRIS_CLIENT_ID",
        "IRIS_CLIENT_SECRET",
        "IRIS_SERVICEBUS_NAMESPACE",
        "IRIS_QUEUE_NAME",
        "BQ_PROJECT",
    ]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        sys.stderr.write("Missing required IRIS env vars: " + ", ".join(missing) + "\n")
        sys.exit(2)


def main():
    # Load local env files if present
    load_env_file(os.path.join(os.getcwd(), "queue_name.env"))
    load_env_file(os.path.join(os.getcwd(), "api.env"))
    ensure_iris_env()

    # Defer import until after env is set
    import asyncio
    import importlib.util
    import pathlib

    script_path = pathlib.Path(os.getcwd()) / "ingest_iris_stream.py"
    if not script_path.exists():
        sys.stderr.write(f"Cannot find {script_path}.\n")
        sys.exit(2)
    spec = importlib.util.spec_from_file_location(
        "ingest_iris_stream", str(script_path)
    )
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore
    # Run its main()
    try:
        asyncio.run(mod.main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
