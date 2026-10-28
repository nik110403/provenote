import csv
import datetime as dt
import importlib.machinery
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "plugins/provenote/bin/lit-search"
FIX = ROOT / "tests/fixtures/search"

loader = importlib.machinery.SourceFileLoader("lit_search", str(TOOL))
spec = importlib.util.spec_from_loader("lit_search", loader)
ls = importlib.util.module_from_spec(spec)
loader.exec_module(ls)

NOW = dt.datetime(2026, 10, 9, 12, 0, tzinfo=dt.timezone.utc)


def fx(name):
    return (FIX / name).read_text(encoding="utf-8")


def fake_fetch(routes, fail=()):
    def f(url, accept="application/json", **kw):
        if kw.get("headers"):
            f.headers[url] = kw["headers"]
        for key, body in routes.items():
            if key in url:
                if key in fail:
                    raise RuntimeError("HTTP 503")
                return body
        raise RuntimeError("unrouted " + url)
    f.headers = {}
    return f


ROUTES = {"api.openalex.org": fx("openalex.json"), "api.semanticscholar.org": fx("s2.json")}


class Parse(unittest.TestCase):
    def test_openalex_doi_normalised_and_retraction(self):
        items = ls.parse_openalex(json.loads(fx("openalex.json")))
        self.assertEqual(items[0]["doi"], "10.1000/alpha")
        self.assertTrue(items[1]["retracted"])
        self.assertEqual(items[0]["refs"], ["W2001", "W2002"])


class Dedupe(unittest.TestCase):
    def merged(self):
        items = ls.parse_openalex(json.loads(fx("openalex.json"))) + ls.parse_s2(json.loads(fx("s2.json")))
        return ls.dedupe(items)

    def test_doi_and_title_dedupe(self):
        m = self.merged()
        # 6 raw -> alpha (by DOI, case-insensitive), credibility (by title), beta, gamma
        self.assertEqual(len(m), 4)
        alpha = next(x for x in m if x["doi"] == "10.1000/alpha")
        self.assertEqual(set(alpha["indexes"]), {"openalex", "semanticscholar"})
        self.assertEqual(alpha["citations"], 400)

    def test_retraction_survives_merge(self):
        self.assertEqual([x["title"] for x in self.merged() if x["retracted"]],
                         ["Retracted Inflation Result"])


class Scoring(unittest.TestCase):
    def test_components_and_order(self):
        m = ls.dedupe(ls.parse_openalex(json.loads(fx("openalex.json"))) + ls.parse_s2(json.loads(fx("s2.json"))))
        out = ls.score(m, 2026, {"openalex": 3, "semanticscholar": 3})
        self.assertEqual(out[0]["doi"], "10.1000/alpha")
        for it in out:
            self.assertAlmostEqual(it["score"], it["s_rel"] + it["s_cpy"] + it["s_rec"], places=2)
            self.assertTrue(0 <= it["s_cpy"] <= 1 and 0 <= it["s_rec"] <= 1)
        old = next(x for x in out if x["doi"] == "10.1000/gamma")
        new = next(x for x in out if x["year"] == 2024)
        self.assertGreater(new["s_rec"], old["s_rec"])


class Run(unittest.TestCase):
    def test_outputs_and_receipt(self):
        with tempfile.TemporaryDirectory() as t:
            r, items, stem = ls.run_search("Money & Prices", 2000, 25, None, Path(t), fake_fetch(ROUTES), NOW, "polite-contact")
            self.assertEqual(stem, "2026-10-09-money-prices")
            self.assertEqual(r["status"], "ok")
            self.assertEqual(r["counts"]["received"], 6)
            self.assertEqual(r["counts"]["after_dedupe"], 4)
            self.assertEqual(r["endpoints"]["openalex"]["params"]["filter"], "from_publication_date:2000-01-01")
            self.assertEqual(r["endpoints"]["openalex"]["mailto"], "set")
            self.assertEqual(r["provider_status"], {"openalex": "READY", "semanticscholar": "READY"})
            with open(Path(t) / (stem + ".csv"), encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 4)
            self.assertEqual([x["status"] for x in rows].count("RETRACTED"), 1)
            md = (Path(t) / (stem + ".md")).read_text(encoding="utf-8")
            self.assertIn("RETRACTED", md)
            self.assertEqual(json.loads((Path(t) / (stem + ".receipt.json")).read_text(encoding="utf-8"))["query"], "Money & Prices")

    def test_one_index_down_is_partial(self):
        with tempfile.TemporaryDirectory() as t:
            r, items, _ = ls.run_search("q", None, 25, None, Path(t),
                                        fake_fetch(ROUTES, fail=("api.semanticscholar.org",)), NOW)
            self.assertEqual(r["status"], "partial")
            self.assertEqual(r["provider_status"]["semanticscholar"], "UNAVAILABLE")
            self.assertEqual(len(items), 3)

    def test_both_down_is_failed(self):
        with tempfile.TemporaryDirectory() as t:
            r, items, _ = ls.run_search("q", None, 25, None, Path(t),
                                        fake_fetch(ROUTES, fail=tuple(ROUTES)), NOW)
            self.assertEqual(r["status"], "failed")
            self.assertEqual(items, [])

    def test_snowball_adds_references(self):
        routes = dict(ROUTES)
        routes["filter=openalex"] = fx("refs.json")
        routes["filter=cites"] = fx("refs.json")  # same record from both directions: deduped
        # order matters: specific filter routes must match before the generic host route
        ordered = {k: routes[k] for k in ("filter=openalex", "filter=cites", "api.openalex.org", "api.semanticscholar.org")}
        with tempfile.TemporaryDirectory() as t:
            r, items, _ = ls.run_search("q", None, 25, 1, Path(t), fake_fetch(ordered), NOW)
            self.assertEqual(r["snowball"]["seeds"], 1)
            self.assertIn("10.1000/delta", [i["doi"] for i in items])
            self.assertEqual(len([i for i in items if i["doi"] == "10.1000/delta"]), 1)

    def test_snowball_ranking_by_citations_per_year(self):
        routes = {"filter=openalex": fx("refs.json"), "filter=cites": fx("snowball.json"),
                  "api.openalex.org": fx("openalex.json"), "api.semanticscholar.org": fx("s2.json")}
        with tempfile.TemporaryDirectory() as t:
            _, items, _ = ls.run_search("q", None, 25, 1, Path(t), fake_fetch(routes), NOW)
        sb = [i for i in items if i["doi"].startswith("10.1000/sb-")]
        self.assertEqual(len(sb), 3)
        # ranked by citations per year (2026 basis): high 2000/9, mid 200/5, low 60/17
        self.assertEqual([i["doi"] for i in sb], ["10.1000/sb-high", "10.1000/sb-mid", "10.1000/sb-low"])


class Http(unittest.TestCase):
    def opener(self, codes):
        calls = []

        class R:
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def read(s): return b"ok"

        def op(req, timeout=0):
            calls.append(1)
            c = codes[len(calls) - 1] if len(calls) <= len(codes) else 200
            if c != 200:
                raise ls.urllib.error.HTTPError(req.full_url, c, "x", {}, None)
            return R()
        return op, calls

    def test_retry_once_then_ok(self):
        op, calls = self.opener([429])
        waits = []
        self.assertEqual(ls.http_get("http://x", opener=op, sleep=waits.append), "ok")
        self.assertEqual((len(calls), waits), (2, [3]))

    def test_retry_only_once(self):
        op, calls = self.opener([503, 503, 503])
        with self.assertRaises(RuntimeError):
            ls.http_get("http://x", opener=op, sleep=lambda s: None)
        self.assertEqual(len(calls), 2)

    def test_no_retry_on_404(self):
        op, calls = self.opener([404])
        with self.assertRaises(RuntimeError):
            ls.http_get("http://x", opener=op, sleep=lambda s: None)
        self.assertEqual(len(calls), 1)

    def test_snowball_stops_after_three_failures(self):
        n = []

        def f(url, accept="application/json"):
            if "filter=" in url:
                n.append(1)
                raise RuntimeError("HTTP 503")
            return ROUTES["api.openalex.org" if "openalex" in url else "api.semanticscholar.org"]
        with tempfile.TemporaryDirectory() as t:
            r, _, _ = ls.run_search("q", None, 25, 3, Path(t), f, NOW)
        self.assertEqual(len(n), 3)
        self.assertEqual(r["provider_status"]["openalex"], "DEGRADED")


class Privacy(unittest.TestCase):
    def test_mailto_never_written(self):
        with tempfile.TemporaryDirectory() as t:
            r, _, stem = ls.run_search("q", None, 25, None, Path(t), fake_fetch(ROUTES), NOW, "secret-addr")
            self.assertEqual(r["endpoints"]["openalex"]["mailto"], "set")
            for f in Path(t).iterdir():
                self.assertNotIn("secret-addr", f.read_text(encoding="utf-8"))


class ApiKey(unittest.TestCase):
    def test_header_sent_to_s2_only_and_key_not_recorded(self):
        fetch = fake_fetch(ROUTES)
        with tempfile.TemporaryDirectory() as t:
            r, _, _ = ls.run_search("q", None, 25, None, Path(t), fetch, NOW, "", "s3cr3t-key")
            self.assertEqual(r["endpoints"]["semanticscholar"]["api_key"], "set")
            for f in Path(t).iterdir():
                self.assertNotIn("s3cr3t-key", f.read_text(encoding="utf-8"))
        self.assertEqual(list(fetch.headers.values()), [{"x-api-key": "s3cr3t-key"}])
        self.assertIn("api.semanticscholar.org", list(fetch.headers)[0])

    def test_no_header_without_key(self):
        fetch = fake_fetch(ROUTES)
        with tempfile.TemporaryDirectory() as t:
            r, _, _ = ls.run_search("q", None, 25, None, Path(t), fetch, NOW)
        self.assertEqual(fetch.headers, {})
        self.assertEqual(r["endpoints"]["semanticscholar"]["api_key"], "unset")


class BibExport(unittest.TestCase):
    def test_append_dedupe_and_unresolved(self):
        def fetch(url, accept="application/json"):
            self.assertEqual(accept, "application/x-bibtex")
            if url.endswith("10.1000/alpha"):
                return fx("bibtex.bib")
            raise RuntimeError("HTTP 404")
        with tempfile.TemporaryDirectory() as t:
            bib = Path(t) / "07_references/references.bib"
            added, skipped, failed = ls.export_bib(["https://doi.org/10.1000/alpha", "10.1000/nope"], bib, fetch)
            self.assertEqual(len(added), 1)
            self.assertEqual([d for d, _ in failed], ["10.1000/nope"])
            self.assertIn("@article{example2018money", bib.read_text(encoding="utf-8"))
            added, skipped, failed = ls.export_bib(["10.1000/alpha"], bib, fetch)
            self.assertEqual((len(added), len(skipped)), (0, 1))
            self.assertEqual(bib.read_text(encoding="utf-8").count("@article"), 1)

    def test_key_collision_gets_suffix_and_doi_match_is_exact(self):
        def fetch(url, accept="application/json"):
            # every DOI resolves to an entry with the same citation key
            doi = url.rsplit("doi.org/", 1)[1]
            return "@article{same2020,\n\tdoi = {%s},\n\ttitle = {T},\n}" % doi
        with tempfile.TemporaryDirectory() as t:
            bib = Path(t) / "refs.bib"
            bib.write_text("@article{same2020,\n\tdoi = {10.1000/alpha2},\n}\n", encoding="utf-8")
            # 10.1000/alpha is a substring of the existing 10.1000/alpha2: must NOT count as present
            added, skipped, failed = ls.export_bib(["10.1000/alpha", "10.1000/beta", "10.1000/alpha2"], bib, fetch)
            self.assertEqual((len(added), len(skipped), len(failed)), (2, 1, 0))
            text = bib.read_text(encoding="utf-8")
            for key in ("same2020,", "same2020a,", "same2020b,"):
                self.assertEqual(text.count("{" + key), 1, key)

    def test_suffix_sequence(self):
        taken = {"k"} | {"k" + chr(97 + i) for i in range(26)}
        self.assertEqual(ls._suffixed("k", {"k"}), "ka")
        self.assertEqual(ls._suffixed("k", taken), "kaa")


if __name__ == "__main__":
    unittest.main()
