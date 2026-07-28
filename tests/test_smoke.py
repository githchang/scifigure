from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'scripts'/'scifigure.py'
DEMO=ROOT/'examples'/'demo_ir.json'


class SciFigureSmokeTest(unittest.TestCase):
    def run_cli(self,*args: str) -> subprocess.CompletedProcess[str]:
        proc=subprocess.run(['python',str(CLI),*args],cwd=ROOT,text=True,capture_output=True)
        if proc.returncode!=0:
            self.fail(f'command failed: {proc.args}\nstdout={proc.stdout}\nstderr={proc.stderr}')
        return proc

    def test_validate_and_preview_all_styles(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'preview'
            self.run_cli('validate-ir','--ir',str(DEMO))
            self.run_cli('preview','--ir',str(DEMO),'--output',str(out),'--thumb-width','360')
            pngs=sorted(p for p in out.glob('preview_*.png') if p.name[:9].startswith('preview_') and len(p.name.split('_')) >= 3 and p.name.split('_')[1].isdigit())
            self.assertEqual(6,len(pngs))
            self.assertTrue((out/'preview_contact_sheet.png').exists())
            manifest=json.loads((out/'preview_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(6,len(manifest['styles']))
            for p in pngs:
                self.assertGreater(p.stat().st_size,5000)

    def test_finalize_creates_editable_package(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'finalized'
            self.run_cli('finalize','--ir',str(DEMO),'--style','s6-paperbanana-soft','--output',str(out))
            final=out/'final'
            for ext in ('png','svg','vsdx'):
                p=final/f'figure_final.{ext}'
                self.assertTrue(p.exists(),p)
                self.assertGreater(p.stat().st_size,1000)
            with ZipFile(final/'figure_final.vsdx') as z:
                names=set(z.namelist())
                self.assertIn('visio/pages/page1.xml',names)
                page=z.read('visio/pages/page1.xml').decode('utf-8')
                self.assertIn('Node_text_input',page)
                self.assertIn('<Connect ',page)

    @unittest.skipUnless(shutil.which('libreoffice'),'LibreOffice is not installed')
    def test_vsdx_is_importable_by_libreoffice(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'finalized'
            self.run_cli('finalize','--ir',str(DEMO),'--style','s5-rigorous-graph','--output',str(out),'--scale','1')
            export=Path(td)/'pdf';export.mkdir()
            proc=subprocess.run(['libreoffice','--headless','--convert-to','pdf','--outdir',str(export),str(out/'final'/'figure_final.vsdx')],text=True,capture_output=True,timeout=90)
            self.assertEqual(0,proc.returncode,proc.stdout+proc.stderr)
            self.assertTrue((export/'figure_final.pdf').exists())


if __name__=='__main__':
    unittest.main()
