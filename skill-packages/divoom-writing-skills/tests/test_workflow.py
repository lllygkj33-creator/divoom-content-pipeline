import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1] / 'skills/divoom-article-workflow'
spec = importlib.util.spec_from_file_location('workflow', BASE / 'scripts/workflow.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def profile():
    p = w.load(BASE / 'config/site.json')
    p['word_count'] = {'min': 1, 'max': 10000}  # Short fixtures exercise contracts, not editorial quality.
    return p


def body():
    return '<article class="divoom-editorial-article"><p>First direct answer.</p><p>Scope and boundaries.</p>' + ''.join(f'<h2 id="section-{i}">Question {i}</h2><p>Supported example statement {i}.</p>' for i in range(1,5)) + '</article>'


def article():
    return {'blog title':'Why Pixel Art Displays Look Different at a Distance', 'url':'pixel-art-displays-at-a-distance', 'meta title':'Pixel Art Displays at a Distance', 'meta description':'Understand distance and visible pixels.', 'summary':'A practical explanation of distance and visible pixels.', 'author':'Divoom Professional Team', 'blog':'Technology Hub', 'tags':['Smart Pixel Displays'], 'html代码':body()}


def add_editorial_plan(outline):
    case = next(x for x in w.load(BASE / 'references/technology-cases.json')['cases'] if x['fx'] == outline['fx'])
    outline.update(editorial_protocol_version=2,
                   sample_review={'fx':outline['fx'], 'url':case['registered_url'], 'status':'snapshot_only',
                                  'checked_at':None, 'visual_inspection':'none', 'reason':'Contract fixture, not an actual source audit.',
                                  'adopt':['Fixture structural observation.'], 'avoid':['Do not copy product facts.']},
                   scenario_plan={'needed':False,'reason':'Fixture exercises contracts, not scenario quality.','cases':[]},
                   faq_decision={'include':False,'reason':'Fixture has no unresolved additional question.','questions':[]},
                   visual_plan=[], visual_reason='Fixture has no provided assets; no fabricated image.')
    for section in outline['sections']:
        section.update(format='prose',format_reason='Fixture explanatory paragraph.',transition='Fixture independent next question.')
    return outline


def populate(run, p, enhanced=True):
    a = article()
    w.init_run(run, a['blog title'])
    outline = {'title':a['blog title'], 'type':'technology', 'fx':'F7', 'blog':a['blog'], 'core_term':'pixel art displays', 'tags':a['tags'], 'answer':'Conditional explanation.', 'scope':'Perception, not buying or setup.', 'sections':[{'id':f'section-{i}', 'h2':f'Question {i}', 'question':'An independent subquestion.', 'new_information':'A distinct variable.', 'claim_ids':['C1'], 'boundary':'Specified conditions.'} for i in range(1,5)]}
    if enhanced:
        add_editorial_plan(outline)
    else:
        state=w.load(run/'run.json');state.pop('editorial_contract_version');w.write_json(run/'run.json',state)
    w.write_json(run / 'outline.json', outline)
    evidence = [{'id':'C1','claim':'Fixture support','body_excerpt':'Supported example statement 1.','status':'supported','reason':'Contract fixture, not a publication claim.','sources':[{'url':'https://www.example.org/specification','path':'','locator':'Fixture section','checked_at':'2026-10-16T00:00:00+00:00','supports':'Fixture support only.'}]}]
    w.write_json(run / 'evidence.json', evidence)
    w.seal(run,'outline',p)
    w.write_json(run / 'metadata.json', {k:v for k,v in a.items() if k != 'html代码'})
    (run / 'body.html').write_text(a['html代码'],encoding='utf-8')
    w.seal(run,'draft',p)
    w.write_json(run / 'links.json', [])
    w.seal(run,'links',p)
    review = {'decision':'pass','reviewer':'test-fixture-not-real-review','scores':{d:8 for d in w.DIMENSIONS},'rationales':{d:'Fixture rationale; not a real article evaluation.' for d in w.DIMENSIONS},'hard_issues':[],'claim_coverage':{'complete':True,'reason':'Fixture only.'},'checks':{c:True for c in w.CHECKS},'revision_notes':[]}
    if enhanced:
        review['editorial_checks']={key:{'decision':'pass','section':'whole-article','reason':'Mechanical fixture only, not completed semantic review.'} for key in w.EDITORIAL_CHECKS}
    w.write_json(run / 'review.json',review)
    w.seal(run,'review',p)


class ArticleValidation(unittest.TestCase):
    def check_bad(self, transform, expected):
        a = article()
        transform(a)
        errors = w.validate_article(a, profile())
        self.assertTrue(any(expected in e for e in errors), errors)

    def test_valid_minimal_contract(self):
        self.assertEqual(w.validate_article(article(), profile()), [])

    def test_required_field(self):
        self.check_bad(lambda a:a.pop('summary'), 'Missing field')

    def test_no_publication_fields(self):
        for key in ('published','published_at','schedule','status'):
            self.check_bad(lambda a:a.update({key:False}), 'Unexpected output field')

    def test_slug(self):
        for slug in ('Bad-slug','bad_slug','/pages/slug','https://divoom.com/blogs/x/y','中文'):
            self.check_bad(lambda a:a.update(url=slug), 'slug')

    def test_utf16_limits(self):
        self.check_bad(lambda a:a.update(summary='😀' * 81), 'UTF-16')
        a = article(); a['summary'] = 'a' * 160
        self.assertEqual(w.validate_article(a,profile()), [])

    def test_blog_and_tags(self):
        self.check_bad(lambda a:a.update(blog='Example Blog A'), 'Unknown blog')
        self.check_bad(lambda a:a.update(tags=['knowledge']), 'registered category')
        self.check_bad(lambda a:a.update(tags=['Smart Pixel Displays']*2), 'Duplicate tags')

    def test_h1_h3_script(self):
        for tag in ('h1','h3','script','iframe'):
            self.check_bad(lambda a:a.update({'html代码':body()+f'<{tag}>bad</{tag}>'}), 'not allowed')

    def test_image_attributes(self):
        self.check_bad(lambda a:a.update({'html代码':body()+'<img src="/image.jpg" alt="">'}), 'src/alt/title')

    def test_external_attributes(self):
        self.check_bad(lambda a:a.update({'html代码':body()+'<a href="https://standards.example.org/report" title="Report">report</a>'}), 'External a')

    def test_relative_link_and_owned_domain(self):
        for url in ('/collections/pixel-display','https://divoom.com/collections/pixel-display','https://www.divoom.com/collections/pixel-display'):
            a=article(); a['html代码']+=f'<a href="{url}" title="Pixel displays">pixel displays</a>'
            self.assertEqual(w.validate_article(a, profile()), [])

    def test_host_spoofing(self):
        self.assertFalse(w.is_internal('https://divoom.com.evil.example/path',profile()))
        self.assertFalse(w.is_internal('//evil.example/path',profile()))
        self.check_bad(lambda a:a.update({'html代码':body()+'<a href="//evil.example/path" title="Bad">bad</a>'}), 'Invalid href')

    def test_executable_links(self):
        for url in ('javascript:alert(1)','data:text/html,bad','https://good.example@evil.example'):
            self.check_bad(lambda a:a.update({'html代码':body()+f'<a href="{url}" title="Bad">bad</a>'}), 'Invalid href')

    def test_event_attributes(self):
        self.check_bad(lambda a:a.update({'html代码':body()+'<p onclick="bad()">text</p>'}), 'Executable')

    def test_unresolved_variables(self):
        self.check_bad(lambda a:a.update({'html代码':body()+'<p>${storefront.domain}</p>'}), 'placeholder')

    def test_preview_link(self):
        self.check_bad(lambda a:a.update({'html代码':body()+'<a href="/?preview_theme_id=1" title="Preview">preview</a>'}), 'Preview')

    def test_malformed_markup(self):
        self.check_bad(lambda a:a.update({'html代码':body()+'<p><strong>broken</p></strong>'}), 'Mismatched')

    def test_id_and_h2_checks(self):
        self.check_bad(lambda a:a.update({'html代码':body().replace('section-4','section-1')}), 'duplicate')
        self.check_bad(lambda a:a.update({'html代码':body().replace(' id="section-4"','')}), 'section id')
        self.check_bad(lambda a:a.update({'html代码':body().replace('<h2 id="section-4">Question 4</h2>','')}), 'four')

    def test_self_link(self):
        self.check_bad(lambda a:a.update({'html代码':body()+'<a href="/blogs/tech-hub/pixel-art-displays-at-a-distance" title="This article">this article</a>'}), 'Self-link')

    def test_empty_h2(self):
        self.check_bad(lambda a:a.update({'html代码':body().replace('Question 1','')}), 'Empty H2')


class StageContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run = Path(self.temp.name) / 'run'
        self.p = profile()
        populate(self.run,self.p)

    def tearDown(self):
        self.temp.cleanup()

    def test_export_single_array_exact_body(self):
        out = w.export_run(self.run, Path(self.temp.name)/'articles.json', self.p)
        data = w.load(out)
        self.assertIsInstance(data,list)
        self.assertEqual(len(data),1)
        self.assertEqual(data[0]['html代码'],body())
        self.assertEqual(set(data[0]),set(w.REQUIRED))

    def test_content_change_invalidates_review(self):
        file=self.run/'body.html'; file.write_text(body().replace('statement 2','new statement 2'),encoding='utf-8')
        with self.assertRaises(w.ContractError):
            w.export_run(self.run,Path(self.temp.name)/'out.json',self.p)

    def test_metadata_change_invalidates_review(self):
        meta=w.load(self.run/'metadata.json');meta['summary']='Changed summary.';w.write_json(self.run/'metadata.json',meta)
        with self.assertRaises(w.ContractError):
            w.export_run(self.run,Path(self.temp.name)/'out.json',self.p)

    def test_link_only_insertion_preserves_draft_not_review(self):
        updated=body().replace('Supported example statement 2.','Supported <a href="/collections/pixel-display" title="Pixel displays">example statement</a> 2.')
        (self.run/'body.html').write_text(updated,encoding='utf-8')
        _,state=w.read_run(self.run)
        self.assertTrue(w.fresh(self.run,state,'draft',self.p))
        self.assertFalse(w.fresh(self.run,state,'links',self.p))
        entry={'href':'/collections/pixel-display','anchor':'example statement','section':'section-2','kind':'internal','purpose':'Contextual fixture','verification':'verified','checked_at':'2026-10-16T00:00:00Z','source_locator':'Fixture target section'}
        w.write_json(self.run/'links.json',[entry]); w.seal(self.run,'links',self.p)
        with self.assertRaises(w.ContractError):
            w.export_run(self.run,Path(self.temp.name)/'out.json',self.p)
        w.seal(self.run,'review',self.p)
        self.assertEqual(w.load(w.export_run(self.run,Path(self.temp.name)/'out.json',self.p))[0]['html代码'],updated)

    def test_review_change_cannot_be_reused(self):
        review=w.load(self.run/'review.json');review['decision']='revise';w.write_json(self.run/'review.json',review)
        with self.assertRaises(w.ContractError):
            w.seal(self.run,'review',self.p)

    def test_config_change_invalidates(self):
        p=copy.deepcopy(self.p);p['word_count']['min']=2
        with self.assertRaises(w.ContractError):
            w.export_run(self.run,Path(self.temp.name)/'out.json',p)

    def test_evidence_gap(self):
        evidence=w.load(self.run/'evidence.json');evidence[0]['status']='unsupported';w.write_json(self.run/'evidence.json',evidence)
        with self.assertRaises(w.ContractError):
            w.seal(self.run,'draft',self.p)

    def test_evidence_must_match_final_body(self):
        evidence=w.load(self.run/'evidence.json');evidence[0]['body_excerpt']='Text not in this article';w.write_json(self.run/'evidence.json',evidence)
        with self.assertRaises(w.ContractError):
            w.seal(self.run,'draft',self.p)

    def test_link_ledger_is_not_http_status(self):
        parsed=w.parse_body(body()+'<a href="/collections/pixel-display" title="Pixels">pixels</a>',self.p)
        with self.assertRaises(w.ContractError):
            w.validate_links([],parsed,self.p)
        entry={'href':'/collections/pixel-display','anchor':'pixels','section':'section-4','kind':'internal','purpose':'Read','verification':'unverified','checked_at':'2026-10-16T00:00:00Z','source_locator':'HTTP200 only'}
        with self.assertRaises(w.ContractError):
            w.validate_links([entry],parsed,self.p)

    def test_no_ghost_verified_links(self):
        entry={'href':'/collections/pixel-display','anchor':'pixels','section':'section-4','kind':'internal','purpose':'Read','verification':'verified','checked_at':'2026-10-16T00:00:00Z','source_locator':'Target paragraph'}
        with self.assertRaises(w.ContractError):
            w.validate_links([entry],w.parse_body(body(),self.p),self.p)

    def test_score_threshold_not_overridden_by_pass_label(self):
        review=w.load(self.run/'review.json');review['scores']['expertise']=6.5
        with self.assertRaises(w.ContractError):
            w.validate_review(review)
        review['scores']['expertise']=7
        with self.assertRaises(w.ContractError):
            w.validate_review(review)

    def test_boolean_is_not_score(self):
        review=w.load(self.run/'review.json');review['scores']['expertise']=True
        with self.assertRaises(w.ContractError):w.validate_review(review)

    def test_type_namespaces(self):
        outline=w.load(self.run/'outline.json');outline['type']='setup'
        with self.assertRaises(w.ContractError):w.validate_outline(outline,self.p)

    def test_no_overwrite_of_internal_artifact(self):
        with self.assertRaises(w.ContractError):
            w.export_run(self.run,self.run/'metadata.json',self.p)

    def test_idempotent_reseal_retains_review(self):
        w.seal(self.run,'draft',self.p)
        w.export_run(self.run,Path(self.temp.name)/'out.json',self.p)

    def test_revision_budget(self):
        for n in range(2):
            (self.run/'body.html').write_text(body().replace('statement 2',f'statement revision-{n} 2'),encoding='utf-8')
            if n == 0:w.seal(self.run,'draft',self.p)
            else:
                with self.assertRaises(w.ContractError):w.seal(self.run,'draft',self.p)

    def test_outline_reseal_does_not_reset_revision_budget(self):
        for n in range(2):
            outline=w.load(self.run/'outline.json');outline['scope']=f'Updated scope {n}';w.write_json(self.run/'outline.json',outline)
            w.seal(self.run,'outline',self.p)
            if n == 0:w.seal(self.run,'draft',self.p)
            else:
                with self.assertRaises(w.ContractError):w.seal(self.run,'draft',self.p)

    def test_inline_anchor_does_not_split_claim_text(self):
        updated=body().replace('statement 1.','<a href="/collections/pixel-display" title="Pixels">statement 1</a>.')
        parsed=w.parse_body(updated,self.p)
        self.assertIn('Supported example statement 1.',parsed.text)
        w.validate_evidence(w.load(self.run/'evidence.json'),parsed.text,w.load(self.run/'outline.json'))


if __name__ == '__main__':
    unittest.main()
