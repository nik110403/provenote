import csv
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent / "plugins/provenote/bin/check-docx"
SOURCE = (
    Path(__file__).resolve().parent.parent
    / "examples/basic/02_sources/md/lei2023financial.md"
)
MANIFEST = (
    Path(__file__).resolve().parent.parent / "examples/basic/02_sources/manifest.csv"
)
QUOTE = "Firstly, while previous studies predominantly address the role of labor market flexibility in financial crisis repercussions at a theoretical level, this paper offers empirical validation."
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def docx(path, text, extra=""):
    runs = "".join(f"<w:r><w:t>{x}</w:t></w:r>" for x in text)
    body = f'<w:document xmlns:w="{W}"><w:body><w:p>{runs}</w:p>{extra}<w:sectPr/></w:body></w:document>'
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", body)


def docx_parts(path, document, **parts):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", document)
        for name, value in parts.items():
            z.writestr("word/" + name + ".xml", value)


class CheckDocx(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = Path(self.t.name) / "project"
        (self.root / "02_sources/md").mkdir(parents=True)
        shutil.copy2(SOURCE, self.root / "02_sources/md/lei2023financial.md")
        shutil.copy2(MANIFEST, self.root / "02_sources/manifest.csv")
        self.doc = Path(self.t.name) / "lecture.docx"
        docx(self.doc, ["“" + QUOTE[:80], QUOTE[80:] + "”"])

    def tearDown(self):
        self.t.cleanup()

    def toolrun(self, *args):
        return subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "--root",
                str(self.root),
                *map(str, args),
                str(self.doc),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def inventory(self):
        inv = Path(self.t.name) / "inventory.csv"
        r = self.toolrun("--inventory", inv)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return inv

    def bindings(self, mutate=None):
        inv = self.inventory()
        with inv.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            r["source_md"], r["page"] = "02_sources/md/lei2023financial.md", "2"
        if mutate:
            mutate(rows)
        p = Path(self.t.name) / "bindings.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=rows[0])
            w.writeheader()
            w.writerows(rows)
        return p

    def test_split_runs_inventory_and_verified_mapping_preserve_input(self):
        before = hashlib.sha256(self.doc.read_bytes()).hexdigest()
        b = self.bindings()
        r = self.toolrun("--bindings", b, "--report", Path(self.t.name) / "report")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("QUOTE_MATCH", r.stdout)
        self.assertEqual(before, hashlib.sha256(self.doc.read_bytes()).hexdigest())

    def test_wrong_page_fake_stale_duplicate_and_missing_fail(self):
        for change in (
            lambda rows: rows[0].update(page="1"),
            lambda rows: rows[0].update(
                quote="fake quote with five whole ordinary words"
            ),
            lambda rows: rows[0].update(document_sha256="0"),
            lambda rows: rows.append(rows[0].copy()),
        ):
            b = self.bindings(change)
            self.assertEqual(self.toolrun("--bindings", b).returncode, 1)
            b.unlink()
            (Path(self.t.name) / "inventory.csv").unlink()
        b = self.inventory()
        self.assertEqual(self.toolrun("--bindings", b).returncode, 1)

    def test_source_tamper_fails(self):
        b = self.bindings()
        source = self.root / "02_sources/md/lei2023financial.md"
        source.write_text(
            source.read_text(encoding="utf-8") + "tamper", encoding="utf-8"
        )
        self.assertEqual(self.toolrun("--bindings", b).returncode, 1)

    def test_tracked_paragraph_content_and_unsupported_nonzero(self):
        docx_parts(
            self.doc,
            f'''<w:document xmlns:w="{W}"><w:body><w:p>
          <w:del><w:r><w:delText>“deleted words that must never count here”</w:delText></w:r></w:del>
          <w:ins><w:r><w:t>“{QUOTE}”</w:t></w:r></w:ins></w:p><w:sectPr/></w:body></w:document>''',
        )
        inv = self.inventory()
        with inv.open(encoding="utf-8") as f:
            self.assertEqual([r["quote"] for r in csv.DictReader(f)], [QUOTE])
        # A field is content-bearing and must downgrade coverage even if a quote was found.
        docx(self.doc, ["“" + QUOTE + "”"], '<w:fldSimple w:instr=" CITATION x "/>')
        inv = Path(self.t.name) / "field.csv"
        self.assertEqual(self.toolrun("--inventory", inv).returncode, 1)

    def test_referenced_footnote_and_endnote_are_inventory_content(self):
        body = f'<w:document xmlns:w="{W}"><w:body><w:p><w:r><w:footnoteReference w:id="1"/></w:r><w:r><w:endnoteReference w:id="2"/></w:r></w:p><w:sectPr/></w:body></w:document>'
        notes = f'<w:footnotes xmlns:w="{W}"><w:footnote w:id="1"><w:p><w:r><w:t>“{QUOTE}”</w:t></w:r></w:p></w:footnote></w:footnotes>'
        ends = f'<w:endnotes xmlns:w="{W}"><w:endnote w:id="2"><w:p><w:r><w:t>“{QUOTE}”</w:t></w:r></w:p></w:endnote></w:endnotes>'
        with zipfile.ZipFile(self.doc, "w") as z:
            z.writestr("word/document.xml", body)
            z.writestr("word/footnotes.xml", notes)
            z.writestr("word/endnotes.xml", ends)
        inv = self.inventory()
        with inv.open(encoding="utf-8") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 2)

    def test_note_binding_requires_correct_part_unique_id_and_ignores_cross_type(self):
        body = f'<w:document xmlns:w="{W}"><w:body><w:p><w:r><w:footnoteReference w:id="1"/></w:r></w:p><w:sectPr/></w:body></w:document>'
        foot = f'<w:footnotes xmlns:w="{W}"><w:footnote w:id="1"><w:p><w:r><w:t>“{QUOTE}”</w:t></w:r></w:p></w:footnote></w:footnotes>'
        end = f'<w:endnotes xmlns:w="{W}"><w:endnote w:id="1"><w:p><w:r><w:t>“{QUOTE}”</w:t></w:r></w:p></w:endnote></w:endnotes>'
        docx_parts(self.doc, body, footnotes=foot, endnotes=end)
        with self.inventory().open(encoding="utf-8") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 1)
        duplicate = foot.replace(
            "</w:footnotes>", foot.split(">", 1)[1] + "</w:footnotes>"
        )
        for i, parts in enumerate(
            (
                {},
                {"footnotes": f'<w:footnotes xmlns:w="{W}"/>'},
                {"footnotes": duplicate},
            )
        ):
            docx_parts(self.doc, body, **parts)
            self.assertEqual(
                self.toolrun(
                    "--inventory",
                    Path(self.t.name) / ("bad" + str(i) + ".csv"),
                ).returncode,
                1,
            )

    def test_parsed_unsupported_structure_in_utf16_prefixes_and_referenced_notes(self):
        body = f'<x:document xmlns:x="{W}"><x:body><x:p><x:r><x:t>“{QUOTE}”</x:t></x:r><x:fldChar x:fldCharType="begin"/></x:p><x:sectPr/></x:body></x:document>'
        foot = f'<q:footnotes xmlns:q="{W}"><q:footnote q:id="1"><q:p><q:r><q:instrText>citation</q:instrText></q:r></q:p></q:footnote></q:footnotes>'
        end = f'<q:endnotes xmlns:q="{W}"><q:endnote q:id="2"><q:p><q:drawing/></q:p></q:endnote></q:endnotes>'
        body = body.replace(
            "<x:r><x:t>",
            '<x:r><x:footnoteReference x:id="1"/><x:endnoteReference x:id="2"/><x:t>',
        )
        with zipfile.ZipFile(self.doc, "w") as z:
            z.writestr("word/document.xml", b"\xff\xfe" + body.encode("utf-16le"))
            z.writestr("word/footnotes.xml", foot)
            z.writestr("word/endnotes.xml", end)
        self.assertEqual(
            self.toolrun("--inventory", Path(self.t.name) / "utf16.csv").returncode, 1
        )

    def test_unsupported_quotes_empty_quotes_and_apostrophes_warn(self):
        for n, text, expected in (
            ("single", f"“{QUOTE}” and ‘fabricated passage’", 1),
            ("straight", f"“{QUOTE}” and 'fabricated passage'", 1),
            ("empty", f'"" “{QUOTE}”', 1),
            ("apostrophe", f"Researchers don't dispute “{QUOTE}”", 0),
        ):
            docx(self.doc, [text])
            self.assertEqual(
                self.toolrun(
                    "--inventory", Path(self.t.name) / (n + ".csv")
                ).returncode,
                expected,
            )

    def test_word_apostrophes_are_not_single_quote_delimiters(self):
        docx(
            self.doc,
            [
                f"Researchers don't dispute and aren't challenging. The researchers' and authors' results agree. “{QUOTE}”"
            ],
        )
        self.assertEqual(
            self.toolrun(
                "--inventory", Path(self.t.name) / "possessive.csv"
            ).returncode,
            0,
        )

    def test_single_quote_candidates_warn_unmatched_and_across_breaks_or_paragraphs(
        self,
    ):
        documents = (
            f"<w:p><w:r><w:t>“{QUOTE}” ‘invented passage</w:t></w:r></w:p>",
            f"<w:p><w:r><w:t>“{QUOTE}” ' invented passage</w:t></w:r></w:p>",
            f"<w:p><w:r><w:t>“{QUOTE}” ‘</w:t></w:r></w:p>",
            f"<w:p><w:r><w:t>“{QUOTE}” ’</w:t></w:r></w:p>",
            f"<w:p><w:r><w:t>“{QUOTE}” '</w:t></w:r></w:p>",
            f"<w:p><w:r><w:t>“{QUOTE}” ‘invented</w:t></w:r><w:r><w:br/></w:r><w:r><w:t>passage’</w:t></w:r></w:p>",
            f"<w:p><w:r><w:t>“{QUOTE}” ‘invented</w:t></w:r></w:p><w:p><w:r><w:t>passage’</w:t></w:r></w:p>",
            f"<w:p><w:r><w:t>“{QUOTE}” ' invented</w:t></w:r></w:p><w:p><w:r><w:t>passage'</w:t></w:r></w:p>",
        )
        for i, content in enumerate(documents):
            body = f'<w:document xmlns:w="{W}"><w:body>{content}<w:sectPr/></w:body></w:document>'
            docx_parts(self.doc, body)
            result = self.toolrun("--inventory", Path(self.t.name) / f"single-{i}.csv")
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("unsupported single-quote delimiter", result.stdout)

    def test_bom_bindings_and_moved_or_deleted_content_use_accepted_view(self):
        body = f'''<w:document xmlns:w="{W}"><w:body><w:p>
          <w:moveFrom><w:r><w:t>“moved-away quote”</w:t></w:r><w:r><w:fldChar w:fldCharType="begin"/></w:r></w:moveFrom>
          <w:moveTo><w:r><w:t>“{QUOTE}”</w:t></w:r></w:moveTo>
          <w:del><w:r><w:instrText>deleted field</w:instrText></w:r></w:del>
          </w:p><w:sectPr/></w:body></w:document>'''
        docx_parts(self.doc, body)
        inv = self.inventory()
        with inv.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([row["quote"] for row in rows], [QUOTE])
        for row in rows:
            row["source_md"], row["page"] = "02_sources/md/lei2023financial.md", "2"
        bindings = Path(self.t.name) / "bom-bindings.csv"
        with bindings.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(rows)
        self.assertEqual(self.toolrun("--bindings", bindings).returncode, 0)

    def test_quote_styles_and_bad_inheritance_warn_without_suppressing_quotes(self):
        doc = f'''<w:document xmlns:w="{W}"><w:body>
          <w:p><w:pPr><w:pStyle w:val="Custom"/></w:pPr><w:r><w:t>undelimited block quote</w:t></w:r></w:p>
          <w:p><w:r><w:t>“{QUOTE}”</w:t></w:r></w:p><w:sectPr/></w:body></w:document>'''
        styles = f'''<w:styles xmlns:w="{W}"><w:style w:type="paragraph" w:styleId="Custom"><w:basedOn w:val="Quote"/></w:style></w:styles>'''
        docx_parts(self.doc, doc, styles=styles)
        result = self.toolrun("--inventory", Path(self.t.name) / "style.csv")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "quotation paragraph style 'Custom' is not extracted", result.stdout
        )
        doc = doc.replace('w:val="Custom"', 'w:val="Cycle"')
        styles = f'''<w:styles xmlns:w="{W}"><w:style w:type="paragraph" w:styleId="Cycle"><w:basedOn w:val="Other"/></w:style><w:style w:type="paragraph" w:styleId="Other"><w:basedOn w:val="Cycle"/></w:style></w:styles>'''
        docx_parts(self.doc, doc, styles=styles)
        result = self.toolrun("--inventory", Path(self.t.name) / "cycle.csv")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "cannot resolve paragraph style 'Cycle' conservatively", result.stdout
        )
        doc = doc.replace('w:val="Cycle"', 'w:val="Broken"')
        styles = f'''<w:styles xmlns:w="{W}"><w:style w:type="paragraph" w:styleId="Broken"><w:basedOn/></w:style><w:style w:type="paragraph" w:styleId="Ordinary"/></w:styles>'''
        docx_parts(self.doc, doc, styles=styles)
        result = self.toolrun("--inventory", Path(self.t.name) / "broken.csv")
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "cannot resolve paragraph style 'Broken' conservatively", result.stdout
        )

    def test_duplicate_paragraph_style_ids_fail_binding_coverage(self):
        doc = f'''<w:document xmlns:w="{W}"><w:body>
          <w:p><w:pPr><w:pStyle w:val="Custom"/></w:pPr><w:r><w:t>undelimited block quote</w:t></w:r></w:p>
          <w:p><w:r><w:t>“{QUOTE}”</w:t></w:r></w:p><w:sectPr/></w:body></w:document>'''
        styles = f'''<w:styles xmlns:w="{W}"><w:style w:type="paragraph" w:styleId="Custom"><w:basedOn w:val="Quote"/></w:style><w:style w:type="paragraph" w:styleId="Custom"/><w:style w:type="paragraph" w:styleId="Normal"/></w:styles>'''
        docx_parts(self.doc, doc, styles=styles)
        inv = Path(self.t.name) / "duplicate-style.csv"
        inventory = self.toolrun("--inventory", inv)
        self.assertEqual(inventory.returncode, 1, inventory.stdout + inventory.stderr)
        self.assertIn(
            "ambiguous duplicate paragraph style id 'Custom'", inventory.stdout
        )
        self.assertIn(
            "cannot resolve paragraph style 'Custom' conservatively", inventory.stdout
        )
        with inv.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([row["quote"] for row in rows], [QUOTE])
        for row in rows:
            row["source_md"], row["page"] = "02_sources/md/lei2023financial.md", "2"
        bindings = Path(self.t.name) / "duplicate-style-bindings.csv"
        with bindings.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0])
            writer.writeheader()
            writer.writerows(rows)
        checked = self.toolrun("--bindings", bindings)
        self.assertEqual(checked.returncode, 1, checked.stdout + checked.stderr)
        self.assertIn("PASS body:2:0 QUOTE_MATCH", checked.stdout)
        self.assertIn("ambiguous duplicate paragraph style id 'Custom'", checked.stdout)

        normal = doc.replace('w:val="Custom"', 'w:val="Normal"')
        docx_parts(
            self.doc,
            normal,
            styles=f'''<w:styles xmlns:w="{W}"><w:style w:type="paragraph" w:styleId="Normal"/></w:styles>''',
        )
        self.assertEqual(
            self.toolrun(
                "--inventory", Path(self.t.name) / "normal-style.csv"
            ).returncode,
            0,
        )

    def test_default_quote_style_and_long_inheritance_chain_warn_without_traceback(
        self,
    ):
        doc = f'''<w:document xmlns:w="{W}"><w:body>
          <w:p><w:r><w:t>undelimited default quote</w:t></w:r></w:p>
          <w:p><w:r><w:t>“{QUOTE}”</w:t></w:r></w:p><w:sectPr/></w:body></w:document>'''
        styles = f'''<w:styles xmlns:w="{W}"><w:style w:type="paragraph" w:styleId="Quote"/><w:style w:type="paragraph" w:styleId="Custom" w:default="1"><w:basedOn w:val="Quote"/></w:style></w:styles>'''
        docx_parts(self.doc, doc, styles=styles)
        result = self.toolrun("--inventory", Path(self.t.name) / "default-style.csv")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(
            "quotation paragraph style 'Custom' is not extracted", result.stdout
        )
        chain = (
            "".join(
                f'<w:style w:type="paragraph" w:styleId="S{i}"><w:basedOn w:val="S{i + 1}"/></w:style>'
                for i in range(1100)
            )
            + '<w:style w:type="paragraph" w:styleId="S1100"><w:basedOn w:val="Quote"/></w:style>'
        )
        doc = doc.replace(
            "<w:p><w:r><w:t>undelimited default quote</w:t></w:r></w:p>",
            '<w:p><w:pPr><w:pStyle w:val="S0"/></w:pPr><w:r><w:t>undelimited quote</w:t></w:r></w:p>',
        )
        styles = f'<w:styles xmlns:w="{W}"><w:style w:type="paragraph" w:styleId="Quote"/>{chain}</w:styles>'
        docx_parts(self.doc, doc, styles=styles)
        result = self.toolrun("--inventory", Path(self.t.name) / "long-chain.csv")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("RecursionError", result.stderr + result.stdout)

    def test_multiple_default_paragraph_styles_warn(self):
        doc = f'<w:document xmlns:w="{W}"><w:body><w:p><w:r><w:t>“{QUOTE}”</w:t></w:r></w:p><w:sectPr/></w:body></w:document>'
        styles = f'''<w:styles xmlns:w="{W}"><w:style w:type="paragraph" w:styleId="Quote" w:default="1"/><w:style w:type="paragraph" w:styleId="Normal" w:default="1"/></w:styles>'''
        docx_parts(self.doc, doc, styles=styles)
        result = self.toolrun(
            "--inventory", Path(self.t.name) / "multiple-defaults.csv"
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ambiguous multiple default paragraph styles", result.stdout)

    def test_tables_live_headers_and_unsupported_live_content_are_covered(self):
        table = f'''<w:document xmlns:w="{W}"><w:body><w:tbl><w:tr><w:tc><w:p><w:r><w:t>“{QUOTE}”</w:t></w:r></w:p></w:tc></w:tr></w:tbl><w:sectPr/></w:body></w:document>'''
        docx_parts(self.doc, table)
        self.assertEqual(
            self.toolrun("--inventory", Path(self.t.name) / "table.csv").returncode, 0
        )
        for name, content in (
            (
                "header1.xml",
                f'<w:hdr xmlns:w="{W}"><w:p><w:r><w:t>header</w:t></w:r></w:p></w:hdr>',
            ),
            (
                "footer1.xml",
                f'<w:ftr xmlns:w="{W}"><w:p><w:r><w:t>footer</w:t></w:r></w:p></w:ftr>',
            ),
        ):
            docx_parts(self.doc, table, **{name[:-4]: content})
            self.assertEqual(
                self.toolrun(
                    "--inventory", Path(self.t.name) / (name + ".csv")
                ).returncode,
                1,
            )
        for name, content in (
            (
                "textbox",
                "<w:txbxContent><w:p><w:r><w:t>hidden</w:t></w:r></w:p></w:txbxContent>",
            ),
            ("drawing", "<w:drawing/>"),
            ("altchunk", '<w:altChunk w:id="rId1"/>'),
        ):
            docx(self.doc, [f"“{QUOTE}”"], content)
            self.assertEqual(
                self.toolrun(
                    "--inventory", Path(self.t.name) / (name + ".csv")
                ).returncode,
                1,
            )

    def test_moved_note_references_follow_the_accepted_view(self):
        body = f'''<w:document xmlns:w="{W}"><w:body><w:p>
          <w:moveFrom><w:r><w:footnoteReference w:id="99"/></w:r></w:moveFrom>
          <w:moveTo><w:r><w:footnoteReference w:id="1"/></w:r></w:moveTo>
          </w:p><w:sectPr/></w:body></w:document>'''
        notes = f'''<w:footnotes xmlns:w="{W}"><w:footnote w:id="1"><w:p><w:r><w:t>“{QUOTE}”</w:t></w:r></w:p></w:footnote></w:footnotes>'''
        docx_parts(self.doc, body, footnotes=notes)
        with self.inventory().open(encoding="utf-8") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 1)

    def test_known_unsupported_quote_delimiters_warn_beside_valid_quote(self):
        for n, unsupported in (
            ("guillemets", "«fabricated passage with five ordinary words»"),
            ("low", "„fabricated passage with five ordinary words“"),
            ("cjk", "「fabricated passage with five ordinary words」"),
        ):
            docx(self.doc, [f"“{QUOTE}” and {unsupported}"])
            inv = Path(self.t.name) / (n + ".csv")
            result = self.toolrun("--inventory", inv)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("unsupported quotation delimiter", result.stdout)
            with inv.open(encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual([row["quote"] for row in rows], [QUOTE])
            for row in rows:
                row["source_md"], row["page"] = "02_sources/md/lei2023financial.md", "2"
            bindings = Path(self.t.name) / (n + "-bindings.csv")
            with bindings.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0])
                writer.writeheader()
                writer.writerows(rows)
            checked = self.toolrun("--bindings", bindings)
            self.assertEqual(checked.returncode, 1, checked.stdout + checked.stderr)
            self.assertIn(
                "FAIL coverage body paragraph 1: unsupported quotation delimiter",
                checked.stdout,
            )

    def test_cjk_delimiter_report_survives_non_utf8_stdout(self):
        docx(
            self.doc, [f"“{QUOTE}” and 「fabricated passage with five ordinary words」"]
        )
        env = dict(os.environ, PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
        result = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "--root",
                str(self.root),
                "--inventory",
                str(Path(self.t.name) / "cp.csv"),
                str(self.doc),
            ],
            capture_output=True,
            env=env,
        )
        out = result.stdout.decode("utf-8") + result.stderr.decode("utf-8")
        self.assertEqual(result.returncode, 1, out)
        self.assertIn(
            "FAIL coverage body paragraph 1: unsupported quotation delimiter(s) '「', '」'",
            out,
        )
        self.assertNotIn("UnicodeEncodeError", out)

    def test_csv_formula_encoding_round_trips_before_integrity_checks(self):
        dangerous = "=1+1 " + QUOTE
        docx(self.doc, ["“" + dangerous + "”"])
        inv = self.inventory()
        with inv.open(encoding="utf-8") as f:
            row = next(csv.DictReader(f))
        self.assertEqual(row["quote"], "'" + dangerous)
        row["source_md"], row["page"] = "'02_sources/md/lei2023financial.md", "2"
        b = Path(self.t.name) / "dangerous-bindings.csv"
        with b.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=row)
            w.writeheader()
            w.writerow(row)
        # A dangerous quote is safely encoded but decoded before its digest is checked.
        self.assertEqual(self.toolrun("--bindings", b).returncode, 1)
        with b.open(encoding="utf-8") as f:
            self.assertTrue(next(csv.DictReader(f))["quote"].startswith("'="))

    def test_malformed_and_hostile_archives_fail(self):
        for name, content in (
            ("bad", b"not zip"),
            (
                "dtd",
                f"\xff\xfe<\x00!\x00D\x00O\x00C\x00T\x00Y\x00P\x00E\x00 x\x00>\x00".encode(
                    "latin1"
                ),
            ),
        ):
            p = Path(self.t.name) / (name + ".docx")
            p.write_bytes(content)
            r = subprocess.run(
                [
                    sys.executable,
                    str(TOOL),
                    "--root",
                    str(self.root),
                    "--inventory",
                    str(Path(self.t.name) / (name + ".csv")),
                    str(p),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(r.returncode, 1)
        p = Path(self.t.name) / "dup.docx"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("word/document.xml", "<x/>")
            z.writestr("word/document.xml", "<x/>")
        r = subprocess.run(
            [
                sys.executable,
                str(TOOL),
                "--root",
                str(self.root),
                "--inventory",
                str(Path(self.t.name) / "dup.csv"),
                str(p),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 1)
