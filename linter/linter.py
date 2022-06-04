def lint_dict(source_code: dict):
    lint_errors = {}
    for name, content in source_code.items():
        if name.endswith('.c') or name.endswith('.cpp') or name.endswith('.go'):
            try:
                lint_result = lint_code(content)
            except Exception as e:
                print(e)
                lint_result = {}
            if len(lint_result) > 0:
                lint_errors[name] = lint_result
    return lint_errors


def lint_errors_to_str(lint_errors: dict):
    str_lint = ''
    for file, errors in lint_errors.items():
        str_lint += '--- ' + file + ':\n'
        for error in errors:
            str_lint += '* Line {}: {}\n'.format(error['line'], error['error'])
        str_lint += '\n'
    # removing the last \n that is not needed
    return str_lint[0:-1]


def lint_code(code: str):
    errors = []

    indent_level = 0
    space_length = None

    line_number = 0
    for line in code.split('\n'):
        line_number += 1

        if len(line) == 0:
            continue

        is_string = False
        is_comment = False

        current_indent = 0
        indent_symbol = None
        need_indentation_check = True
        checking_indentation = True

        prev_c = None
        c = None
        next_c = line[0]

        indent_level_diff_pos = 0
        indent_level_diff_neg = 0
        len_line = len(line)
        for i in range(0, len_line):
            prev_c, c, next_c = None if c is None else c, next_c, None if i == len_line - 1 else line[i + 1]

            if not is_comment and c == '"' and prev_c != '\\':
                is_string = False if is_string else True

            if not is_string and c == '/' and next_c == '/':
                is_comment = True

            if not is_string and not is_comment:
                if c == '{':
                    indent_level_diff_pos += 1
                elif c == '}':
                    indent_level_diff_neg -= 1

            if checking_indentation:
                if c != '\t' and c != ' ':
                    if space_length is None and indent_symbol == ' ' and indent_level > 0:
                        space_length = current_indent / indent_level
                    checking_indentation = False
                    continue
                if indent_symbol is not None and c != indent_symbol:
                    need_indentation_check = False
                    errors.append({
                        'line': line_number,
                        'error': 'indentation/mix'
                    })
                    checking_indentation = False
                indent_symbol = c
                current_indent += 1
            elif not is_string and not is_comment and c == ',':
                before_space = i > 0 and line[i - 1] == ' '
                no_space = i < len_line - 1 and line[i + 1] != ' '
                extra_space = i < len_line - 2 and line[i + 2] == ' '
                if before_space or no_space or extra_space:
                    errors.append({
                        'line': line_number,
                        'error': 'spaces/punctuation'
                    })

        indent_level += indent_level_diff_neg

        if need_indentation_check:
            expected_indent = indent_level
            if indent_symbol == ' ' and space_length is not None:
                expected_indent *= space_length
            if current_indent != expected_indent and need_indentation_check:
                errors.append({
                    'line': line_number,
                    'error': 'indentation/bad'
                })

        indent_level += indent_level_diff_pos

    if len(code) > 0 and code[-1] != '\n':
        errors.append({
            'line': line_number,
            'error': 'line/noendnewline'
        })

    return errors
