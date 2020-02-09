PAGE_SIZE = 10
TOP_SIZE = 50


def get_require_str(require_fields, rename_dict):
    require_fields_str = ''
    for field in require_fields:
        if field not in rename_dict:
            require_fields_str += field
        else:
            origin_name, cur_name = rename_dict[field], field
            require_fields_str += '{} as {}'.format(origin_name, cur_name)
        require_fields_str += ', '
    require_fields_str = require_fields_str[:-2]
    return require_fields_str
