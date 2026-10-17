import copy
import unittest
from test_workflow import w, profile, body, article, add_editorial_plan


def visual():
    return {'id':'bass-figure','role':'explanatory','section':'section-1','aspect_ratio':'16:9',
            'filename':'bass-figure.png','prompt':'Draw a generic speaker diagram with clearly identified parts. No model-specific claims.',
            'alt':'Generic loudspeaker diagram','title':'Speaker parts','asset_status':'pending','src':'',
            'after_paragraph':1,'purpose':'Explain components','claim_ids':['C1']}


def outline():
    return {'image_prompt_delivery':'html_comments_v1','sections':[{'id':'section-1'},{'id':'section-2'}],'visual_plan':[visual()]}


class ImagePromptHandoff(unittest.TestCase):
    def test_prompt_is_metadata_not_visible_article_text(self):
        fragment=body().replace('<p>Supported example statement 1.</p>','<p>Supported example statement 1.</p>'+w.render_image_prompt(visual()))
        parsed=w.parse_body(fragment,profile())
        self.assertEqual(parsed.errors,[])
        self.assertEqual(parsed.text,w.parse_body(body(),profile()).text)
        self.assertEqual(len(parsed.image_prompts),1)
        w.validate_prompt_delivery(outline(),parsed)
        a=article();a['html代码']=fragment
        self.assertEqual(w.validate_article(a,profile()),[])

    def test_unknown_comments_remain_forbidden(self):
        parsed=w.parse_body(body()+'<!-- ordinary editorial note -->',profile())
        self.assertTrue(parsed.errors)

    def test_missing_prompt_cannot_pass_delivery(self):
        with self.assertRaisesRegex(w.ContractError,'missing'):
            w.validate_prompt_delivery(outline(),w.parse_body(body(),profile()))

    def test_edited_prompt_cannot_reuse_plan(self):
        changed=visual();changed['prompt']='An unreviewed replacement instruction.'
        parsed=w.parse_body(body().replace('<p>Supported example statement 1.</p>','<p>Supported example statement 1.</p>'+w.render_image_prompt(changed)),profile())
        with self.assertRaisesRegex(w.ContractError,'sealed plan'):
            w.validate_prompt_delivery(outline(),parsed)

    def test_prompt_is_bound_to_actual_section(self):
        parsed=w.parse_body(body().replace('<p>Supported example statement 2.</p>','<p>Supported example statement 2.</p>'+w.render_image_prompt(visual())),profile())
        with self.assertRaisesRegex(w.ContractError,'planned section'):
            w.validate_prompt_delivery(outline(),parsed)

    def test_comment_delimiters_and_html_are_escaped(self):
        row=visual();row['prompt']='Literal notation --><h1> is not executable markup.'
        encoded=w.render_image_prompt(row)
        self.assertNotIn('<h1>',encoded)
        self.assertEqual(encoded.count('-->'),1)
        parsed=w.parse_body(encoded,profile())
        self.assertEqual(parsed.errors,[])
        self.assertEqual(parsed.image_prompts[0]['payload']['prompt'],row['prompt'])

    def test_prompt_changes_are_part_of_draft_fingerprint(self):
        first=visual();second=copy.deepcopy(first);second['prompt']='A revised composition.'
        self.assertNotEqual(w.parse_body(w.render_image_prompt(first),profile()).semantic_text,
                            w.parse_body(w.render_image_prompt(second),profile()).semantic_text)

    def test_image_prompt_without_delivery_contract_is_rejected(self):
        parsed=w.parse_body(w.render_image_prompt(visual()),profile())
        with self.assertRaisesRegex(w.ContractError,'explicit outline'):
            w.validate_prompt_delivery({'sections':[]},parsed)


if __name__=='__main__':
    unittest.main()
