""" Tests for creating and updating command templates """
import httpie.cli.argtemplate
import tempfile
import json
from .utils import http


class TestStoreTemplate:

    def test_store_normal_template_with_method(self):
        """
        Tests that a valid template can be stored properly when the template contains a method parameter
        """

        with tempfile.NamedTemporaryFile('w+', delete=False) as temp_fp:

            httpie.cli.argtemplate.TEMPLATE_FILE = temp_fp.name

            command = 'http template test_template GET https://catfact.ninja/fact param1=value1 param2=value2'
            args = command.split()

            httpie.cli.argtemplate.store_json_template(args[2:])

            stored_templates = json.load(temp_fp)
            assert stored_templates[args[2]] is not None

            template = stored_templates[args[2]]
            assert template['method'] == args[3]
            assert template['url'] == args[4]
            assert template['data'] is not None

            template_data = template['data']
            assert template_data['param1'] == 'value1'
            assert template_data['param2'] == 'value2'

    def test_store_normal_template_without_method(self):
        """
        Tests that a valid template can be stored properly when the template doesn't contain a method parameter
        """

        with tempfile.NamedTemporaryFile('w+', delete=False) as temp_fp:

            httpie.cli.argtemplate.TEMPLATE_FILE = temp_fp.name

            command = 'http template test_template https://catfact.ninja/fact param1=value1 param2=value2'
            args = command.split()

            httpie.cli.argtemplate.store_json_template(args[2:])

            stored_templates = json.load(temp_fp)
            assert stored_templates[args[2]] is not None

            template = stored_templates[args[2]]
            assert template['method'] == None
            assert template['url'] == args[3]
            assert template['data'] is not None

            template_data = template['data']
            assert template_data['param1'] == 'value1'
            assert template_data['param2'] == 'value2'

    def test_store_template_overwrites_old_template_same_name(self):
        """
        Tests that storing a template with the same name as an already existing template will overwrite the existing template
        """
        with tempfile.NamedTemporaryFile('w+', delete=False) as temp_fp:

            httpie.cli.argtemplate.TEMPLATE_FILE = temp_fp.name

            command = 'http template test_template GET https://catfact.ninja/fact param1=value1 param2=value2'
            args = command.split()

            httpie.cli.argtemplate.store_json_template(args[2:])

            old_stored_templates = json.load(temp_fp)

            command = 'http template test_template POST https://catfact.ninja/fact param1=value2 param2=value1'
            args = command.split()
            httpie.cli.argtemplate.store_json_template(args[2:])

            temp_fp.seek(0)
            new_stored_templates = json.load(temp_fp)

            assert len(old_stored_templates) == len(new_stored_templates)
            assert new_stored_templates[args[2]]['method'] == 'POST'
            assert new_stored_templates[args[2]]['data']['param1'] == 'value2'
            assert new_stored_templates[args[2]]['data']['param2'] == 'value1'

    def test_store_template_invalid_method(self):
        """
        Tests that storing a template with an invalid method argument leads to the template being saved without a method parameter
        """
        with tempfile.NamedTemporaryFile('w+', delete=False) as temp_fp:
            httpie.cli.argtemplate.TEMPLATE_FILE = temp_fp.name

            command = 'http template test_template NOT_VALID_METHOD https://catfact.ninja/fact param1=value1 param2=value2'
            args = command.split()

            httpie.cli.argtemplate.store_json_template(args[2:])

            stored_templates = json.load(temp_fp)
            print(stored_templates)
            template = stored_templates[args[2]]
            assert template['method'] is None

class TestEditTemplate:
    def test_edit_template_update_value(self):
        """
        Tests that the edit_json_template function can correctly update a value
        """
        with tempfile.NamedTemporaryFile('w+', delete=False) as temp_fp:
            httpie.cli.argtemplate.TEMPLATE_FILE = temp_fp.name

            command = 'http template test_template GET https://catfact.ninja/fact param1=value1 param2=value2'
            args = command.split()

            httpie.cli.argtemplate.store_json_template(args[2:])

            httpie.cli.argtemplate.edit_json_template(['test_template', 'param1', 'newvalue1'])

            stored_templates = json.load(temp_fp)
            assert stored_templates[args[2]] is not None

            template = stored_templates[args[2]]
            assert template['method'] == 'GET'
            assert template['url'] == args[4]
            assert template['data'] is not None

            template_data = template['data']
            assert template_data['param1'] == 'newvalue1'
            assert template_data['param2'] == 'value2'
