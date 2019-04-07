from collections import Counter
from os import path
from jinja2 import Environment, PackageLoader
import yaml


pl = PackageLoader('tenzing', 'templates')
jinja2_env = Environment(lstrip_blocks=True, trim_blocks=True, loader=pl)

template_map = [
    'overview.html',
    'base.html',
    'list_composition.html'
]
template_map = {file: jinja2_env.get_template(file) for file in template_map}


yaml_template_file = path.join(path.dirname(__file__), 'templates', 'default_report_config.yaml')
default_template = yaml.load(open(yaml_template_file), Loader=yaml.FullLoader)


def traverse_config(config, summary):
    if isinstance(config, list):
        list_cmp_template = template_map['list_composition.html']
        return list_cmp_template.render(data=[traverse_config(subconfig, summary) for subconfig in config])
    elif isinstance(config, dict):
        if config.get('is_abstract_variable', False):
            list_cmp_template = template_map['list_composition.html']
            html_list = []
            for title, val_dict in summary.get(config['data']).items():
                new_data = {'title': summary.get('col_type_map')[title], 'data': val_dict}
                html = template_map[config['template']].render(data=new_data)
                new_data['title'] = title
                new_data['data'] = html

                html_list.append(new_data)

            result = list_cmp_template.render(data=html_list)
            return result

        elif 'template' in config and 'data' in config:
            template = template_map[config['template']]
            data = config.copy()
            data.pop('template')
            data['data'] = summary.get(config['data'])
            return template.render(data=data)
        else:
            return {key: traverse_config(value, summary) for key, value in config.items()}


def process_yaml_template(template):
    if isinstance(template, list):
        return [process_yaml_template(subtemp) for subtemp in template]
    elif isinstance(template, dict):
        new_template = {}
        for key, values in template.items():
            if 'template' in values and 'data' in values:
                values.update({'title': key})
                new_template[key] = values
            else:
                new_template[key] = process_yaml_template(values)
        return new_template


class summary_report:
    def __init__(self, col_type_map, column_summary, general_summary, template=default_template):
        self.column_summary = {k: self.prettify(v) for k, v in column_summary.items()}
        self.general_summary = self.prettify(general_summary)
        self.col_type_map = col_type_map
        self.type_counts = Counter(self.col_type_map.values())
        self.template = process_yaml_template(template)

    @staticmethod
    def prettify(dict_):
        print(dict_)
        return {key: v if not isinstance(v, float) else round(v, 2) for key, v in dict_.items()}

    def generate_html(self):
        base_template = template_map['base.html']
        data = traverse_config(self.template, self)
        return base_template.render(data=data)

    def get(self, attr):
        return getattr(self, attr)