""" Tests for creating and updating command templates """
import httpie.cli.argtemplate
import tempfile
import json
import pytest


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
            template = stored_templates[args[2]]
            assert template is not None
            assert template['url'] == args[4]
            assert template['method'] is None
            assert template['data']['param1'] == 'value1'
            assert template['data']['param2'] == 'value2'


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

    def test_edit_template_add_method(self):
        """
        Tests that you can edit a template and add a method when there previously was none
        """
        with tempfile.NamedTemporaryFile('w+', delete=False) as temp_fp:
            httpie.cli.argtemplate.TEMPLATE_FILE = temp_fp.name

            command = 'http template test_template https://catfact.ninja/fact param1=value1 param2=value2'
            args = command.split()

            httpie.cli.argtemplate.store_json_template(args[2:])

            httpie.cli.argtemplate.edit_json_template(['test_template', 'method', 'POST'])

            stored_templates = json.load(temp_fp)
            assert len(stored_templates) == 1
            assert stored_templates[args[2]] is not None

            template = stored_templates[args[2]]
            assert template['method'] == 'POST'
            assert template['url'] == args[3]
            assert template['data'] is not None

    def test_edit_template_change_url(self):
        """
        Tests that you can change the URL of a template
        """
        with tempfile.NamedTemporaryFile('w+', delete=False) as temp_fp:
            httpie.cli.argtemplate.TEMPLATE_FILE = temp_fp.name

            command = 'http template test_template GET https://catfact.ninja/fact param1=value1 param2=value2'
            args = command.split()

            httpie.cli.argtemplate.store_json_template(args[2:])

            httpie.cli.argtemplate.edit_json_template(['test_template', 'url', 'https://fake-url/'])

            stored_templates = json.load(temp_fp)
            assert len(stored_templates) == 1
            assert stored_templates[args[2]] is not None

            template = stored_templates[args[2]]
            assert template['method'] == 'GET'
            assert template['url'] == 'https://fake-url/'
            assert template['data'] is not None

    def test_edit_template_not_found(self, capsys):
        """
        Tests that an exception is raised when trying to edit a template that doesn't exist
        """
        with tempfile.NamedTemporaryFile('w+', delete=False) as temp_fp:
            httpie.cli.argtemplate.TEMPLATE_FILE = temp_fp.name

            with pytest.raises(Exception):
                httpie.cli.argtemplate.edit_json_template(['test_template', 'param', 'value'])
                out, _ = capsys.readouterr()
                assert "Template 'test_template' does not exist." in out

    def test_edit_template_key_not_found(self):
        """
        Tests that you can add new key-value pairs to an existing template
        """
        with tempfile.NamedTemporaryFile('w+', delete=False) as temp_fp:
            httpie.cli.argtemplate.TEMPLATE_FILE = temp_fp.name

            command = 'http template test_template GET https://catfact.ninja/fact param1=value1 param2=value2'
            args = command.split()

            httpie.cli.argtemplate.store_json_template(args[2:])
            old_stored_templates = json.load(temp_fp)
            assert old_stored_templates[args[2]]['data']['param2'] is None

            httpie.cli.argtemplate.edit_json_template(['test_template', 'param2', 'value2'])
            new_stored_templates = json.load(temp_fp)
            assert new_stored_templates[args[2]]['data']['param2'] == 'value2'


class TestLoadTemplate:
    def test_load_template(self):
        """
        Tests that loading a template yields the same arguments that were passed (except for 'http template <name>')
        """
        with tempfile.NamedTemporaryFile('w+', delete=False) as temp_fp:
            httpie.cli.argtemplate.TEMPLATE_FILE = temp_fp.name

            command = 'http template test_template GET https://catfact.ninja/fact param1=value1 param2=value2'
            args = command.split()

            httpie.cli.argtemplate.store_json_template(args[2:])
            loaded_args = httpie.cli.argtemplate.load_template(args[2])

            for i in range(len(args) - 3):
                assert args[i + 3] == loaded_args[i]

    def test_load_template_not_found(self, capsys):
        """
        Tests loading a template when the name of the template to load cannot be found in the template file
        """
        with tempfile.NamedTemporaryFile('w+', delete=False) as temp_fp:
            httpie.cli.argtemplate.TEMPLATE_FILE = temp_fp.name

            command = 'http template test_template GET https://catfact.ninja/fact param1=value1 param2=value2'
            args = command.split()

            loaded_args = httpie.cli.argtemplate.load_template(args[2])
            out, _ = capsys.readouterr()
            assert loaded_args == []
            assert "Template 'test_template' does not exist." in out