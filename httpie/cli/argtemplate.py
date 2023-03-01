import argparse
import json
import sys

def store_json_template(args):
    """
    Store a template as a string in templates.json, the format for running this is:
        http template <name> |<method>| <url> login=testuser password=testpassword ...
    """
    template_name = args.pop(0)
    template_method = None
    template_url = None
    template_variables = {}
    
    if ["CONNECT", "DELETE", "GET", "HEAD", "OPTIONS", "POST", "PUT", "TRACE", "PATCH"].__contains__(args[0]):
        template_method = args.pop(0)
        template_url = args.pop(0)
    else:
        template_url = args.pop(0)
    
    for arg in args:
        variable_name, variable_value = arg.split("=")
        template_variables[variable_name] = variable_value

    template = {}
    template['method'] = template_method
    template['url'] = template_url
    template['data'] = template_variables
    with open("httpie/cli/templates.json", "r+") as f:
        stored_templates = {}
        try:
            stored_templates = json.load(f)
        except json.JSONDecodeError:
            pass
        if template_name in stored_templates:
            stored_templates.pop(template_name)
        stored_templates[template_name] = template
        f.seek(0)
        json.dump(stored_templates, f)
        f.truncate()

def edit_json_template(args):
    stored_templates = {}
    with open("httpie/cli/templates.json", "r+") as f:
        try:
            stored_templates = json.load(f)
        except json.JSONDecodeError:
            pass
        template_name = args.pop(0)
        template_item = args.pop(0)
        template_value = args.pop(0)  
        updated_template = {}
        if template_name in stored_templates:
            updated_template = stored_templates.pop(template_name)

        updated_template[template_item] = template_value
        stored_templates[template_name] = updated_template
        f.seek(0)
        json.dump(stored_templates, f) 
        f.truncate()




