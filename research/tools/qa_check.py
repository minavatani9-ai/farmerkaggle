"""Release QA for release/sonnet001/main.py + submission.zip.

Checks (per task spec):
- Python compile
- AST parse
- standalone agent import
- exact kaggle-environments==1.32.7
- dynamic execution (real env.run, not just import)
- zero runtime/schema failures across a validation batch
- ZIP contains exactly one member: main.py
- archived main.py bytes equal exported main.py
- SHA-256 for main.py and submission.zip
"""
import hashlib
import importlib.util
import json
import py_compile
import sys
import zipfile
import ast
import os

RELEASE_DIR = sys.argv[1] if len(sys.argv) > 1 else "."
MAIN_PY = os.path.join(RELEASE_DIR, "main.py")
SUBMISSION_ZIP = os.path.join(RELEASE_DIR, "submission.zip")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    report = {"checks": {}, "errors": []}

    # 1. kaggle_environments version
    try:
        import kaggle_environments as ke
        try:
            from importlib.metadata import version as _pkg_version
            ver = _pkg_version("kaggle-environments")
        except Exception:
            ver = getattr(ke, "__version__", "unknown")
        report["checks"]["kaggle_environments_version"] = ver
        report["checks"]["kaggle_environments_version_ok"] = (ver == "1.32.7")
    except Exception as e:
        report["errors"].append(f"kaggle_environments import failed: {e}")
        report["checks"]["kaggle_environments_version_ok"] = False

    # 2. py_compile
    try:
        py_compile.compile(MAIN_PY, doraise=True)
        report["checks"]["py_compile"] = "OK"
    except Exception as e:
        report["checks"]["py_compile"] = f"FAIL: {e}"
        report["errors"].append(str(e))

    # 3. AST parse
    try:
        src = open(MAIN_PY).read()
        ast.parse(src)
        report["checks"]["ast_parse"] = "OK"
    except Exception as e:
        report["checks"]["ast_parse"] = f"FAIL: {e}"
        report["errors"].append(str(e))

    # 4. standalone import (fresh module, no package context)
    try:
        spec = importlib.util.spec_from_file_location("release_main", MAIN_PY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "agent") and callable(mod.agent)
        report["checks"]["standalone_import"] = "OK"
        report["checks"]["has_agent_callable"] = True
    except Exception as e:
        report["checks"]["standalone_import"] = f"FAIL: {e}"
        report["errors"].append(str(e))
        mod = None

    # 5. dynamic execution: real env.run across several seeds/opponents/seats
    failures = []
    games_run = 0
    if mod is not None:
        try:
            import kaggle_environments as ke
            seeds = [8101, 8102, 8103]
            opponents = ["pass", "random", "starter"]
            for opp in opponents:
                for seed in seeds:
                    for seat in (0, 1):
                        agents = [mod.agent, opp] if seat == 0 else [opp, mod.agent]
                        env = ke.make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
                        env.run(agents)
                        games_run += 1
                        final = env.steps[-1]
                        statuses = [s.status for s in final]
                        if any(s != "DONE" for s in statuses):
                            failures.append({"opp": opp, "seed": seed, "seat": seat, "statuses": statuses})
        except Exception as e:
            failures.append({"exception": str(e)})
    report["checks"]["dynamic_execution_games_run"] = games_run
    report["checks"]["dynamic_execution_failures"] = failures
    report["checks"]["dynamic_execution_ok"] = (len(failures) == 0 and games_run > 0)

    # 6. ZIP structure
    try:
        with zipfile.ZipFile(SUBMISSION_ZIP) as z:
            names = z.namelist()
            report["checks"]["zip_members"] = names
            report["checks"]["zip_single_member_main_py"] = (names == ["main.py"])
            archived_bytes = z.read("main.py")
        with open(MAIN_PY, "rb") as f:
            exported_bytes = f.read()
        report["checks"]["archived_equals_exported"] = (archived_bytes == exported_bytes)
    except Exception as e:
        report["checks"]["zip_single_member_main_py"] = False
        report["errors"].append(str(e))

    # 7. Hashes
    report["checks"]["main_py_sha256"] = sha256_of(MAIN_PY)
    report["checks"]["submission_zip_sha256"] = sha256_of(SUBMISSION_ZIP)

    all_ok = (
        report["checks"].get("kaggle_environments_version_ok")
        and report["checks"].get("py_compile") == "OK"
        and report["checks"].get("ast_parse") == "OK"
        and report["checks"].get("standalone_import") == "OK"
        and report["checks"].get("dynamic_execution_ok")
        and report["checks"].get("zip_single_member_main_py")
        and report["checks"].get("archived_equals_exported")
    )
    report["overall_pass"] = bool(all_ok)

    print(json.dumps(report, indent=2))
    with open(os.path.join(RELEASE_DIR, "SONNET001_QA.json"), "w") as f:
        json.dump(report, f, indent=2)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
