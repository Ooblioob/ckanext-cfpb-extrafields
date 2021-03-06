import re

# Abstracted to simplify unit testing via mock
def Invalid(message):
    import ckan.plugins.toolkit as tk
    raise tk.Invalid(message)

def dedupe_unordered(items):
    return list(set(items))
def contains_bad_chars(str):
    ''' contains <>'''
    test = False
    for c in ['>','<']:
        test = test or (c in str)
    return test
def input_value_validator(value):
    # __Other option is the option that triggers a js event for user-specified option creation
    if "__Other" in value :
        Invalid("'Other, please specify' is not a valid option")
    if contains_bad_chars(value):
        Invalid('multi-select fields cannot contain <, > or quote characters')
    # assume that duplicates are mistakes continue quietly
    if not isinstance(value, basestring):
        value = dedupe_unordered(value)
    return value

# check multiple fields at once
# http://docs.ckan.org/en/latest/extensions/adding-custom-fields.html#custom-validators
def date_to_int(str_date):
    try:
        date = int(str_date.replace('-',''))
    except ValueError:
        Invalid("Please ensure date is in yyyy-mm-dd format!")
    return date
def end_after_start_validator(key, flattened_data, errors, context):
    # errors contains a list of validation errors
    # context has things like 'session' (sqlalchemy session) or 'user' (username of logged-in user)
    for i in range(flattened_data[('__extras',)].get('num_resources',1)):
        start_str = flattened_data.get(('resources', i, 'content_temporal_range_start'),'0')
        end_str = flattened_data.get(('resources', i, 'content_temporal_range_end'),'1')
        if start_str and end_str:
            if date_to_int(start_str) > date_to_int(end_str):
                Invalid("content start date occurs after end date")
    return

def pra_control_num_validator(value):
    PRA_CONTROL_NUM_REGEX = re.compile('^\d{4}-\d{4}$')
    if value and not PRA_CONTROL_NUM_REGEX.match(value):
        Invalid("Must be in the format ####-####")
    return value

def dig_id_validator(value):
    DIG_ID_REGEX = re.compile('^DI\d{5}$')
    if value and not DIG_ID_REGEX.match(value):
        Invalid("Must be in the format DI#####")
    return value

def positive_number_validator(value):
    # feels incredibly verbose... requires code review
    if value:
        try:
            if float(value) < 0:
                Invalid("Must be a positive number")
        except ValueError:
            Invalid("Must be a positive number")
    return value

#ckan.logic.validators.isodate(value, context)
def reasonable_date_validator(value):
    ''' check the year is yyyy-mm-dd and between 1700 and 2300 '''
    import datetime
    try:
        parsed_date = datetime.datetime.strptime(value, '%Y-%m-%d')
        if parsed_date.year < 1700 or parsed_date.year > 2300:
            Invalid("The chosen year is out of range (>1700, <2300).")
    except ValueError:
            Invalid("Please ensure date is in yyyy-mm-dd format.")
    return value

# select multis are contained in unicode strings that look like:
# u'{"blah blah","blah asdf",asdf}' ; u'{asdf,asdf}' ; u'asdf' (see also tests.py)
def clean_select_multi0(a):
    ''' parses the results of an html form select-multi '''
    # this solution doesn't accomodate commas in select-multi fields
    # and validation preventing users from entering commas is not straightforward.
    return a.replace('{', "").replace("}", "").replace("\"","").split(",")
def clean_select_multi(s):
    ''' parses the results of an html form select-multi '''
    # This solution allows commas, but is unpythonic
    if not s:
        return []
    if not isinstance(s, basestring):
        return s
    s = s.lstrip('{').rstrip('}')
    clean = []
    left = 0
    right = 1
    while right < len(s):
        if s[left]=="\"":
            if right+1<len(s) and s[right]=="\"" and s[right+1]==",":
                # reached the end of the quoted patch; append and skip
                clean.append(s[left+1:right])
                left = right+2
                right = right+3
            else:
                right = right+1
        else:
            if s[right]==",":
                # hit a comma: append and skip the comma
                clean.append(s[left:right])
                left = right+1
                right = right+2
            else:
                right = right+1
    if s[left]=="\"":
        # reached the end with a closing quote (don't save the quotes)
        clean.append(s[left+1:-1])
    else:
        clean.append(s[left:])
    return clean

