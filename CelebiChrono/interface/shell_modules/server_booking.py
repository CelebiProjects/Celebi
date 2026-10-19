"""Publish code and collected results to the Celebi bookkeeping server."""
import json
import os
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from CelebiChrono.utils import csys

BOOKKEEP_BATCH_SIZE = 25


def _relay_results(session, relay, base, yuki, server, project_uuid, commit, needed, progress):
    """Publish bounded batches so successful uploads survive a later failure."""
    result = {"uploaded": [], "failed": [], "missing": [], "skipped": []}
    for offset in range(0, len(needed), BOOKKEEP_BATCH_SIZE):
        batch = needed[offset:offset + BOOKKEEP_BATCH_SIZE]
        end = offset + len(batch)
        progress(f"Collecting results {offset + 1}-{end}/{len(needed)} from Yuki...")
        packed = _request(relay, "POST", yuki + "/book-celebi-server/pack",
                          {"project_uuid": project_uuid, "impressions": batch}, timeout=1800)
        entries = packed["packed"]
        if any(entry["uuid"] not in batch for entry in entries):
            raise ValueError("Yuki packed an unrequested impression")
        result["missing"].extend(packed["missing"])
        result["skipped"].extend(packed.get("skipped", []))
        if entries:
            progress(f"Syncing manifest for {len(entries)} archives from batch ending at {end}...")
            manifest = [{**entry, "git_commit": commit} for entry in entries]
            delta = _request(session, "POST", base + "/impressions/sync", {"manifest": manifest})
            selected = {entry["uuid"] for entry in delta["to_upload"]}
            if not selected.issubset({entry["uuid"] for entry in entries}):
                raise ValueError("Server requested an archive not packed by Yuki")
            if selected:
                if not delta["grant"]:
                    raise ValueError("Server did not authorize result uploads")
                progress(f"Uploading {len(selected)} archives via Yuki...")
                uploaded = _request(relay, "POST", yuki + "/book-celebi-server/upload", {
                    "celebi_server_url": server, "project_uuid": project_uuid,
                    "pack_id": packed["pack_id"], "grant": delta["grant"],
                    "archives": [entry for entry in entries if entry["uuid"] in selected]},
                    timeout=1900)
                result["uploaded"].extend(uploaded["uploaded"])
                result["failed"].extend(uploaded["failed"])
        progress(f"Processed {end}/{len(needed)}; uploaded {len(result['uploaded'])}; "
                 f"skipped {len(result['skipped'])}; missing {len(result['missing'])}")
    return result


def project_root(path=""):
    root = csys.project_path(str(Path(path or os.getcwd()).resolve()))
    if not root:
        raise ValueError("Run inside a Celebi project or pass --path")
    return Path(root)

def _git(root, *args):
    process = subprocess.run(["git", *args], cwd=root, capture_output=True,
                             text=True, check=False)
    if process.returncode:
        raise ValueError("git " + args[0] + " failed: " + process.stderr.strip())
    return process.stdout if "-z" in args else process.stdout.strip()

def forbidden(path):
    parts = Path(path).parts
    # .celebi-env contains shareable environment definitions, not installed
    # environments. Keep normal credential/result exclusions inside it too.
    return any(p in ("impressions", "impressions_store", "stageout",
                     ".celebi-workspace", ".celebi-workaround") for p in parts) or (
        Path(path).name in ("config.local.json", "hosts.json", "bookkeeping.local.json",
                           ".env", ".DS_Store") or Path(path).name.startswith(".env.")
    ) or (".celebi" in parts and Path(path).name.startswith("immutable-impress"))

def _url(value):
    value = value if "://" in value else "http://" + value
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username:
        raise ValueError("Expected an HTTP(S) URL without credentials")
    return value.rstrip("/")

def register(server, token, path="", yuki=""):
    root = project_root(path)
    project_uuid = json.loads((root / ".celebi/config.json").read_text())["project_uuid"]
    server = _url(server)
    # Verify the generated analysis password before saving it locally.
    with requests.Session() as session:
        session.headers["Authorization"] = "Bearer " + token
        _request(session, "POST", server + "/api/projects/" + project_uuid +
                 "/bookkeep/authorize")
    target = root / ".celebi/bookkeeping.local.json"
    if _git(root, "ls-files", "--", ".celebi/bookkeeping.local.json"):
        raise ValueError("Remove bookkeeping.local.json from Git tracking first")
    exclude = Path(_git(root, "rev-parse", "--git-path", "info/exclude"))
    if not exclude.is_absolute():
        exclude = root / exclude
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a") as handle:
        handle.write("\n**/.celebi/bookkeeping.local.json\n**/.celebi/config.local.json\n"
                     "**/.celebi/hosts.json\n**/.celebi/impressions/\n**/.celebi/impressions_store/\n"
                     "**/.celebi/immutable-impress*\n")
    target.write_text(json.dumps({"server": server, "token": token, "yuki": _url(yuki) if yuki else ""}))
    target.chmod(0o600)
    return server

def _retry_safe(method, url, body):
    """Retry only reads, delta negotiation, and exact-commit impress admission.

    Do not replay Yuki pack/upload, registration, or arbitrary mutation POSTs.
    """
    if method == "GET":
        return True
    if method != "POST":
        return False
    path = urlparse(url).path
    if re.fullmatch(r"/api/projects/[^/]+/(bookkeep/authorize|impressions/sync)", path):
        return True
    return bool(re.fullmatch(r"/api/projects/[^/]+/impress", path)
                and isinstance(body, dict)
                and isinstance(body.get("git_commit"), str)
                and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", body.get("git_commit", "")))


def _request(session, method, url, body=None, timeout=120):
    method = method.upper()
    attempts = 3 if _retry_safe(method, url, body) else 1
    for attempt in range(attempts):
        try:
            # Git, collection and upload can leave the other Session idle for
            # minutes. Do not carry a keep-alive socket over those boundaries.
            response = session.request(method, url, json=body, timeout=timeout,
                                       headers={"Connection": "close"}, allow_redirects=False)
            break
        except requests.RequestException as exc:
            session.close()  # Discard failed pools, retaining auth headers/cookies.
            transient = (isinstance(exc, requests.ConnectionError)
                         and not isinstance(exc, (requests.exceptions.SSLError, requests.Timeout)))
            if not transient or attempt + 1 == attempts:
                path = urlparse(url).path
                raise ValueError(f"{method} {path}: {type(exc).__name__} after "
                                 f"{attempt + 1} attempt(s); rerun bookkeep to resume") from None
            time.sleep(0.25 * (2 ** attempt))
    if not 200 <= response.status_code < 300:
        try:
            problem = response.json()
            detail = problem.get("detail") or problem.get("title") or problem.get("error")
        except ValueError:
            detail = "HTTP " + str(response.status_code)
        raise ValueError(str(detail))
    return response.json()

def publish_git(root, commit_message=None, tag=None):
    """Stage shareable project changes and push exactly this branch and tag."""
    if Path(_git(root, "rev-parse", "--show-toplevel")).resolve() != root.resolve():
        raise ValueError("The Celebi project must be the Git repository root")
    branch = _git(root, "symbolic-ref", "--short", "HEAD")
    remote = _git(root, "config", "--get", "branch." + branch + ".remote")
    upstream = _git(root, "config", "--get", "branch." + branch + ".merge")
    if remote == "." or not upstream.startswith("refs/heads/"):
        raise ValueError("Configure a GitLab upstream branch before bookkeeping")
    if tag:
        _git(root, "check-ref-format", "refs/tags/" + tag)
        local_tags = _git(root, "tag", "--list", tag)
        remote_tags = _git(root, "ls-remote", "--tags", remote,
                           "refs/tags/" + tag, "refs/tags/" + tag + "^{}")
        if local_tags or remote_tags:
            raise ValueError("Tag already exists: " + tag)
    tracked = _git(root, "ls-files", "-z").split("\0")
    unsafe = [name for name in tracked if name and forbidden(name)]
    if unsafe:
        raise ValueError("Remove local credentials/results from Git tracking first: " + ", ".join(unsafe))
    _git(root, "fetch", remote)
    ahead_behind = _git(root, "rev-list", "--left-right", "--count", "HEAD...@{upstream}").split()
    if int(ahead_behind[1]):
        raise ValueError("Branch is behind or diverged from upstream; reconcile it first")
    changed = _git(root, "diff", "--name-only", "-z", "HEAD").split("\0")
    new = _git(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0")
    paths = sorted({p for p in changed + new if p and not forbidden(p)})
    if paths and not commit_message:
        raise ValueError("Working tree has changes; provide --commit")
    if commit_message:
        if paths:
            _git(root, "add", "-A", "--", *paths)
        if _git(root, "diff", "--cached", "--name-only"):
            _git(root, "commit", "-m", commit_message)
    commit = _git(root, "rev-parse", "HEAD")
    refspecs = ["HEAD:" + upstream]
    if tag:
        _git(root, "tag", tag, commit)
        refspecs.append("refs/tags/" + tag + ":refs/tags/" + tag)
    _git(root, "push", "--atomic", remote, *refspecs)
    return commit

def bookkeep(commit_message=None, tag=None, server="", token="", path="", yuki="",
             allow_partial=False, progress=print):
    """Commit/push, request canonical server impressions, and relay missing results."""
    root = project_root(path)
    settings_path = root / ".celebi/bookkeeping.local.json"
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    server = _url(server or os.environ.get("CELEBI_SERVER_URL") or settings.get("server", ""))
    token = token or os.environ.get("CELEBI_PROJECT_TOKEN") or settings.get("token", "")
    if not token:
        raise ValueError("Register the analysis token with register-celebi-server")
    hosts_path = root / ".celebi/hosts.json"
    hosts = json.loads(hosts_path.read_text()) if hosts_path.exists() else {}
    yuki = _url(yuki or settings.get("yuki") or hosts.get("serverurl", "127.0.0.1:3315"))
    project_uuid = json.loads((root / ".celebi/config.json").read_text())["project_uuid"]
    with requests.Session() as session, requests.Session() as relay:
        session.headers["Authorization"] = "Bearer " + token
        base = server + "/api/projects/" + project_uuid
        # This must stay before publish_git: an invalid token must not create a
        # commit, create a tag, fetch, or push anything.
        authorization = _request(session, "POST", base + "/bookkeep/authorize")
        if not authorization.get("authorized") or authorization.get("project_uuid") != project_uuid:
            raise ValueError("Bookkeeping server returned an invalid authorization response")
        commit = publish_git(root, commit_message, tag)
        progress("Pushed commit " + commit[:10] + ((" · tag " + tag) if tag else ""))
        job = _request(session, "POST", base + "/impress",
                       {"git_commit": commit, "tag": tag}, timeout=1900)
        deadline = time.monotonic() + 1900
        last_report = 0
        while job["status"] in ("pending", "running"):
            now = time.monotonic()
            if now - last_report >= 15:
                stats = job.get("impress_stats", {})
                detail = (f" {stats['processed']}/{stats['total']}; "
                          f"created {stats['created']}; reused {stats['reused']}"
                          if stats else "")
                progress("Server impress: " + job.get("phase", job["status"]) + detail)
                last_report = now
            if time.monotonic() > deadline:
                raise ValueError("Server impress timed out; job " + job["job_id"])
            time.sleep(1)
            job = _request(session, "GET", base + "/impress/" + job["job_id"])
        if job["status"] != "succeeded":
            raise ValueError("Server impress failed: " + str(job.get("error")))
        if job["git_commit"] != commit:
            raise ValueError("Server returned a different commit")
        needed = job["needed_impressions"]
        progress(str(len(job["impressions"])) + " canonical impressions; " + str(len(needed)) + " need results")
        if not needed:
            return {"uploaded": [], "missing": [], "url": server + "/projects/" + project_uuid}
        result = _relay_results(session, relay, base, yuki, server, project_uuid,
                                commit, needed, progress)
        result["url"] = server + "/projects/" + project_uuid
        progress("Uploaded " + str(len(result["uploaded"])) + " archives; missing " +
                 str(len(result["missing"])) + ". Browse: " + result["url"])
        if result["failed"] or (result["missing"] and not allow_partial):
            raise ValueError("Some results are missing or failed; collect results and retry "
                             "(omit --tag when reusing the published commit)")
        return result
