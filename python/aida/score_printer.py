"""
AIDA score printer.
"""
__author__  = "Shahzad Rajput <shahzad.rajput@nist.gov>"
__status__  = "production"
__version__ = "0.0.0.1"
__date__    = "3 February 2020"

from aida.container import Container

class ScorePrinter(Container):
    """
    AIDA score printer.
    """
    
    separators = {
        'pretty': None,
        'tab': '\t',
        'space': ' '
        }
    
    def __init__(self, logger, printing_specs, separator=None):
        super().__init__(logger)
        self.printing_specs = printing_specs
        self.separator = separator
        self.widths = {column.get('name'):len(column.get('header')) for column in printing_specs}
        self.lines = []
        
    def prepare_lines(self):
        widths = self.get('widths')
        scores = self.values()
        for score in scores:
            elements_to_print = {}
            for field in self.printing_specs:
                field_name = field.get('name')
                value = score.get(field_name)
                format_spec = field.get('mean_format') if score.get('summary') and field.get('mean_format') else field.get('format')
                text = '{0:{1}}'.format(value, 's' if value=='' else format_spec)
                elements_to_print[field_name] = text
                widths[field_name] = len(text) if len(text)>widths[field_name] else widths[field_name]
            self.get('lines').append(elements_to_print)
    
    def get_header_text(self):
        return self.get_line_text()
    
    def get_line_text(self, line=None):
        text = ''
        separator = ''
        for field in self.printing_specs:
            text += separator
            field_name = field.get('name')
            value = line.get(field_name) if line is not None else field.get('header')
            num_spaces = 0 if self.separators[self.get('separator')] is not None else self.widths[field_name] - len(str(value))
            spaces_prefix = ' ' * num_spaces if field.get('justify') == 'R' and self.separators[self.get('separator')] is None else ''
            spaces_postfix = ' ' * num_spaces if field.get('justify') == 'L' and self.separators[self.get('separator')] is None else ''
            text = '{}{}{}{}'.format(text, spaces_prefix, value, spaces_postfix)
            separator = ' ' if self.separators[self.get('separator')] is None else self.separators[self.get('separator')]
        return text
    
    def __str__(self):
        self.prepare_lines()
        string = self.get_header_text()
        for line in self.get('lines'):
            string = '{}\n{}'.format(string, self.get_line_text(line))
        return string