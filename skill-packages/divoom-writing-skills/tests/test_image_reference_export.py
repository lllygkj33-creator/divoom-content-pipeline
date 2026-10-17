from pathlib import Path
import tempfile
import unittest
from test_workflow import w, profile, populate
from test_image_prompt_handoff import visual


class ReferenceHandoff(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.run=Path(self.temp.name)/'run'
        self.profile=profile()
        populate(self.run,self.profile)

    def tearDown(self):
        self.temp.cleanup()

    def add_figure(self):
        outline=w.load(self.run/'outline.json')
        row=visual()
        row.update(slot='images_1',reference_mode='product_photos_required',
                   reference_requirement='Upload the intended model in a clear front or three-quarter photograph.',
                   prompt='Use the uploaded product reference as the exterior identity. Ask for the real product photo before generation if missing; do not invent a generic speaker.')
        outline['visual_plan']=[row]
        w.write_json(self.run/'outline.json',outline)
        body=(self.run/'body.html').read_text(encoding='utf-8')
        body=body.replace('<p>Supported example statement 1.</p>','<p>Supported example statement 1.</p>'+w.render_image_slot(row))
        (self.run/'body.html').write_text(body,encoding='utf-8')
        for stage in w.STAGES:
            w.seal(self.run,stage,self.profile)
        return row

    def test_separate_file_uses_sealed_slot_and_requires_attachments(self):
        row=self.add_figure()
        destination=w.export_image_handoff(self.run,Path(self.temp.name)/'image-prompts.txt',self.profile)
        output=destination.read_text(encoding='utf-8')
        for literal in ('请上传','===== images_1 =====',row['filename'],row['alt'],row['prompt'],row['reference_requirement']):
            self.assertIn(literal,output)
        json_file=w.export_run(self.run,Path(self.temp.name)/'articles.json',self.profile)
        self.assertEqual(set(w.load(json_file)[0]),set(w.REQUIRED))

    def test_reference_change_invalidates_both_deliverables(self):
        self.add_figure()
        outline=w.load(self.run/'outline.json')
        outline['visual_plan'][0]['reference_requirement']='A different, unreviewed product mapping.'
        w.write_json(self.run/'outline.json',outline)
        with self.assertRaisesRegex(w.ContractError,'stale'):
            w.export_image_handoff(self.run,Path(self.temp.name)/'prompts.txt',self.profile)
        with self.assertRaises(w.ContractError):
            w.export_run(self.run,Path(self.temp.name)/'articles.json',self.profile)

    def test_missing_reference_decision_cannot_pass(self):
        outline=w.load(self.run/'outline.json')
        outline['visual_plan']=[visual()]
        with self.assertRaisesRegex(w.ContractError,'reference decision'):
            w.validate_prompt_plan(outline)

    def test_text_file_cannot_overwrite_article_json_or_body(self):
        for target in (self.run/'body.html',Path(self.temp.name)/'articles.json'):
            with self.assertRaisesRegex(w.ContractError,'separate .txt'):
                w.export_image_handoff(self.run,target,self.profile)


if __name__=='__main__':
    unittest.main()
