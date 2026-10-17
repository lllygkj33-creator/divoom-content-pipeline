import copy
import unittest
from test_workflow import w, profile, body
from test_image_prompt_handoff import visual, outline


def plan():
    result=outline()
    result['image_slot_delivery']='visible_alt_v1'
    result['visual_plan'][0]['slot']='images_1'
    return result


def fragment(row):
    return body().replace('<p>Supported example statement 1.</p>',
                          '<p>Supported example statement 1.</p>'+w.render_image_slot(row))


class ImageSlotDelivery(unittest.TestCase):
    def test_visible_locator_does_not_inflate_editorial_word_count(self):
        current=plan()
        output=fragment(current['visual_plan'][0])
        self.assertIn('<p>images_1：Generic loudspeaker diagram</p>',output)
        parsed=w.parse_body(output,profile())
        self.assertEqual(parsed.text,w.parse_body(body(),profile()).text)
        self.assertEqual(parsed.errors,[])
        w.validate_prompt_delivery(current,parsed)

    def test_wrong_alt_or_duplicate_slot_is_rejected(self):
        current=plan()
        output=fragment(current['visual_plan'][0])
        for changed in (output.replace('images_1：Generic loudspeaker diagram','images_1：Wrong alt'),
                        output.replace('</article>','<p>images_1：Generic loudspeaker diagram</p></article>')):
            with self.assertRaisesRegex(w.ContractError,'slot number'):
                w.validate_prompt_delivery(current,w.parse_body(changed,profile()))

    def test_skipped_number_and_banner_are_rejected(self):
        for change in ('number','banner'):
            current=plan()
            current['visual_plan'][0]['slot']='images_2' if change=='number' else 'images_1'
            if change=='banner':
                current['visual_plan'][0]['role']='banner'
            with self.assertRaises(w.ContractError):
                w.validate_prompt_plan(current)

    def test_first_ready_image_does_not_renumber_remaining_slots(self):
        current=plan()
        ready=current['visual_plan'][0]
        ready.update(asset_status='ready',src='https://cdn.example.org/real.png')
        pending=copy.deepcopy(ready)
        pending.update(id='second-figure',slot='images_2',asset_status='pending',src='')
        current['visual_plan'].append(pending)
        w.validate_prompt_plan(current)
        w.validate_prompt_delivery(current,w.parse_body(fragment(pending),profile()))

    def test_locator_cannot_supply_evidence_excerpt(self):
        parsed=w.parse_body(fragment(plan()['visual_plan'][0]),profile())
        self.assertNotIn('Generic loudspeaker diagram',parsed.text)
        self.assertIn('images_1',parsed.semantic_text)


if __name__=='__main__':
    unittest.main()
