import importlib.util,json,shutil,tempfile,unittest,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('builder',ROOT/'scripts/build.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
class BuildTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  shutil.copytree(ROOT/'website',self.root/'website')
  for v in builder.EDITIONS:
   (self.root/'chapters'/v).mkdir(parents=True)
   for n in [1,2]:shutil.copy2(ROOT/'chapters'/v/f'{n:04}.xhtml',self.root/'chapters'/v/f'{n:04}.xhtml')
 def tearDown(self):self.temp.cleanup()
 def test_correction_propagates_to_site_and_matching_epub(self):
  builder.build(self.root)
  p=self.root/'chapters/first/0001.xhtml';p.write_text(p.read_text().replace('</body>','<p>Verified correction &amp; punctuation.</p></body>'))
  # A stale generated file must not survive a subsequent build.
  (self.root/'dist/data/first/99.json').write_text('{}')
  builder.build(self.root)
  site=json.loads((self.root/'dist/data/first/1.json').read_text())
  self.assertIn('Verified correction &amp; punctuation.',site['html'])
  self.assertFalse((self.root/'dist/data/first/99.json').exists())
  for v in builder.EDITIONS:
   with zipfile.ZipFile(self.root/f'dist/assets/{v}.epub') as z:
    content=z.read('OEBPS/chapter-1.xhtml').decode()
    self.assertEqual('Verified correction' in content,v=='first')
    builder.verify_epub(self.root/f'dist/assets/{v}.epub',builder.read_chapters(self.root,v))
  self.assertIn('2 chapters',(self.root/'dist/index.html').read_text())
 def test_invalid_source_preserves_last_good_build(self):
  builder.build(self.root);before=(self.root/'dist/assets/revised.epub').read_bytes()
  (self.root/'chapters/revised/0001.xhtml').write_text('<broken>')
  with self.assertRaises(ValueError):builder.build(self.root)
  self.assertEqual(before,(self.root/'dist/assets/revised.epub').read_bytes())
 def test_missing_chapter_fails(self):
  (self.root/'chapters/first/0001.xhtml').unlink()
  with self.assertRaises(ValueError):builder.build(self.root)
 def test_whitespace_after_body_preserves_chapter(self):
  p=self.root/'chapters/revised/0002.xhtml'
  p.write_text(p.read_text().replace('</body>','</body>\n  '))
  expected=''.join(ET.parse(p).getroot().find(builder.NS+'body').itertext())
  builder.build(self.root)
  with zipfile.ZipFile(self.root/'dist/assets/revised.epub') as z:
   actual=ET.fromstring(z.read('OEBPS/chapter-2.xhtml')).find(builder.NS+'body')
   self.assertEqual(''.join(actual.itertext()),expected)
if __name__=='__main__':unittest.main()
