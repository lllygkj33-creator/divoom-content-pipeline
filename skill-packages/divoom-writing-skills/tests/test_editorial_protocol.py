import copy
from pathlib import Path
import tempfile
import unittest
from test_workflow import w, profile, populate, body


class EditorialProtocol(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.run=Path(self.temp.name)/'run'
        self.p=profile()
        populate(self.run,self.p)
        self.outline=w.load(self.run/'outline.json')

    def tearDown(self):
        self.temp.cleanup()

    def test_layout_reference_cannot_replace_fx_sample(self):
        self.outline['sample_review']['url']='https://momcozy.com/blogs/momcare/travel-with-pregnancy'
        with self.assertRaisesRegex(w.ContractError,'registered FX'):
            w.validate_outline(self.outline,self.p)

    def test_no_faq_no_scenes_and_no_images_can_be_valid(self):
        w.validate_outline(self.outline,self.p)
        exported=w.load(w.export_run(self.run,Path(self.temp.name)/'articles.json',self.p))[0]
        self.assertNotIn('visual_plan',exported)
        self.assertNotIn('editorial_checks',exported)
        self.assertEqual(exported['html代码'],body())

    def test_scenario_requires_controlled_conditions(self):
        row={'section':'section-1','condition':'Near a wall','changes':'Reflected sound','reader_signal':'Some notes differ','claim_ids':['C1']}
        self.outline['scenario_plan']={'needed':True,'reason':'One condition changes.','cases':[row]}
        with self.assertRaisesRegex(w.ContractError,'stays_constant'):
            w.validate_outline(self.outline,self.p)
        row['stays_constant']='Same source, settings and listening position.'
        w.validate_outline(self.outline,self.p)

    def test_pending_asset_cannot_be_inserted(self):
        self.outline['image_prompt_delivery']='internal'
        self.outline['image_slot_delivery']='none'
        self.outline['visual_plan']=[{'id':'v1','role':'explanatory','section':'section-1','after_paragraph':1,'purpose':'Fixture map','claim_ids':['C1'],'asset_status':'pending','src':'','reference_mode':'generic_concept_only','reference_requirement':'Abstract fixture, not model-specific construction.'}]
        w.validate_outline(self.outline,self.p)
        parsed=w.parse_body(body().replace('Supported example statement 1.','Supported example statement 1.<img src="https://example.org/figure.png" alt="A schematic" title="A schematic">'),self.p)
        with self.assertRaisesRegex(w.ContractError,'ready visual plan'):
            w.validate_editorial_body(self.outline,parsed)

    def test_ready_asset_is_bound_to_its_section(self):
        self.outline['visual_plan']=[{'id':'v1','role':'explanatory','section':'section-2','after_paragraph':1,'purpose':'Fixture map','claim_ids':['C1'],'asset_status':'ready','src':'https://example.org/figure.png'}]
        parsed=w.parse_body(body().replace('Supported example statement 1.','Supported example statement 1.<img src="https://example.org/figure.png" alt="A schematic" title="A schematic">'),self.p)
        with self.assertRaisesRegex(w.ContractError,'planned section'):
            w.validate_editorial_body(self.outline,parsed)
        self.outline['visual_plan'][0]['section']='section-1'
        w.validate_editorial_body(self.outline,parsed)

    def test_candidate_cannot_be_promoted_by_copying_verified_label(self):
        self.outline['fx']='F14'
        self.outline['sample_review'].update(fx='F14',url='https://momcozy.com/blogs/breastfeeding/heated-breast-massager-mastitis-prevention')
        with self.assertRaisesRegex(w.ContractError,'candidate status'):
            w.validate_outline(self.outline,self.p)
        self.outline['sample_review']['mapping_status']='supplementary_candidate'
        w.validate_outline(self.outline,self.p)

    def test_missing_or_rejected_editorial_review_blocks_export(self):
        review=w.load(self.run/'review.json')
        review['editorial_checks']['paragraph_progression']['decision']='revise'
        with self.assertRaisesRegex(w.ContractError,'paragraph_progression'):
            w.validate_editorial_review(review,self.outline)
        review.pop('editorial_checks')
        with self.assertRaisesRegex(w.ContractError,'records required'):
            w.validate_editorial_review(review,self.outline)

    def test_planning_changes_invalidate_review(self):
        self.outline['visual_reason']='Revised image decision.'
        w.write_json(self.run/'outline.json',self.outline)
        with self.assertRaisesRegex(w.ContractError,'stale'):
            w.export_run(self.run,Path(self.temp.name)/'articles.json',self.p)

    def test_new_technology_run_cannot_skip_editorial_protocol(self):
        self.outline.pop('editorial_protocol_version')
        w.write_json(self.run/'outline.json',self.outline)
        with self.assertRaisesRegex(w.ContractError,'New Technology runs'):
            w.seal(self.run,'outline',self.p)

    def test_source_read_claim_requires_actual_read_timestamp(self):
        self.outline['sample_review']['status']='read'
        self.outline['sample_review']['checked_at']=None
        with self.assertRaisesRegex(w.ContractError,'checked_at'):
            w.validate_outline(self.outline,self.p)

    def test_pending_visual_cannot_smuggle_a_fake_url(self):
        self.outline['visual_plan']=[{'id':'v1','role':'scene','section':'section-1','after_paragraph':0,'purpose':'Fixture','claim_ids':[],'asset_status':'pending','src':'https://example.org/not-created.png'}]
        with self.assertRaisesRegex(w.ContractError,'invented URL'):
            w.validate_outline(self.outline,self.p)

    def test_historical_run_remains_exportable(self):
        legacy=Path(self.temp.name)/'legacy'
        populate(legacy,self.p,enhanced=False)
        self.assertEqual(w.load(w.export_run(legacy,Path(self.temp.name)/'legacy.json',self.p))[0]['html代码'],body())


if __name__=='__main__':
    unittest.main()
