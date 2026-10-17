import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest


class InstalledValidation(unittest.TestCase):
    def test_other_installed_skills_do_not_break_package_integrity_check(self):
        source=Path(__file__).resolve().parents[1]/'skills'
        with tempfile.TemporaryDirectory() as tmp:
            installed=Path(tmp)/'skills'
            for name in ('divoom-article-workflow','divoom-outline','divoom-draft','divoom-links'):
                folder=installed/name
                (folder/'agents').mkdir(parents=True)
                (folder/'SKILL.md').write_text(f'---\nname: {name}\ndescription: Scope regression fixture.\n---\n',encoding='utf-8')
                (folder/'agents/openai.yaml').write_text('interface: {}\n',encoding='utf-8')
            root=installed/'divoom-article-workflow'
            (root/'references').mkdir()
            (root/'references/source-manifest.json').write_text(json.dumps({'files':[]}),encoding='utf-8')
            (root/'scripts').mkdir()
            shutil.copy2(source/'divoom-article-workflow/scripts/validate_package.py',root/'scripts/validate_package.py')
            other=installed/'unrelated-skill'
            other.mkdir()
            (other/'SKILL.md').write_text('Example only: [redlining](references/redlining.md)',encoding='utf-8')
            validator=installed/'divoom-article-workflow/scripts/validate_package.py'
            spec=importlib.util.spec_from_file_location('installed_validation',validator)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            with contextlib.redirect_stdout(io.StringIO()) as output:
                result=module.main()
            self.assertEqual(result,0,output.getvalue())


if __name__=='__main__':
    unittest.main()
