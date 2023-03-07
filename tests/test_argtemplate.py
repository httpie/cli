""" Tests for creating and updating command templates """
import httpie.cli.argtemplate
import tempfile
import json


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
            assert template['method'] is None
            assert template['url'] == args[3]
            assert template['data'] is not None

            template_data = template['data']
            assert template_data['param1'] == 'value1'
            assert template_data['param2'] == 'value2'


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
