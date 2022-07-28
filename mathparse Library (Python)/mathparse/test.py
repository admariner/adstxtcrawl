def parse(string, language=None):
    """
    Return a solution to the equation in the input string.
    """
    if language:
        string = replace_word_tokens(string, language)

    tokens = tokenize(string)
    postfix = to_postfix(tokens)

    return evaluate_postfix(postfix)







def replace_word_tokens(string, language):
    """
    Given a string and an ISO 639-2 language code,
    return the string with the words replaced with
    an operational equivalent.
    """
    words = mathwords.word_groups_for_language(language)

    # Replace operator words with numeric operators
    operators = words['binary_operators'].copy()
    if 'unary_operators' in words:
        operators.update(words['unary_operators'])

    for operator in list(operators.keys()):
        if operator in string:
            string = string.replace(operator, operators[operator])

    # Replace number words with numeric values
    numbers = words['numbers']
    for number in list(numbers.keys()):
        if number in string:
            string = string.replace(number, str(numbers[number]))

    # Replace scaling multipliers with numeric values
    scales = words['scales']
    end_index_characters = mathwords.BINARY_OPERATORS
    end_index_characters.add('(')

    word_matches = find_word_groups(string, list(scales.keys()))

    for match in word_matches:
        string = string.replace(match, f'({match})')

    for scale in list(scales.keys()):
        for _ in range(string.count(scale)):
            start_index = string.find(scale) - 1
            end_index = len(string)

            while is_int(string[start_index - 1]) and start_index > 0:
                start_index -= 1

            end_index = string.find(' ', start_index) + 1
            end_index = string.find(' ', end_index) + 1

            add = ' + '
            if string[end_index] in end_index_characters:
                add = ''

            string = f'{string[:start_index]}({string[start_index:]}'
            string = string.replace(scale, f'* {str(scales[scale])}){add}', 1)

    string = string.replace(') (', ') + (')

    return string



def find_word_groups(string, words):
    """
    Find matches for words in the format "3 thousand 6 hundred 2".
    The words parameter should be the list of words to check for
    such as "hundred".
    """
    scale_pattern = '|'.join(words)
    # For example:
    # (?:(?:\d+)\s+(?:hundred|thousand)*\s*)+(?:\d+|hundred|thousand)+
    regex = re.compile(
        r'(?:(?:\d+)\s+(?:' +
        scale_pattern +
        r')*\s*)+(?:\d+|' +
        scale_pattern + r')+'
    )
    return regex.findall(string)





def tokenize(string, language=None, escape='___'):
    """
    Given a string, return a list of math symbol tokens
    """
    # Set all words to lowercase
    string = string.lower()

    # Ignore punctuation
    if len(string) and not string[-1].isalnum():
        character = string[-1]
        string = f'{string[:-1]} {character}'

    # Parenthesis must have space around them to be tokenized properly
    string = string.replace('(', ' ( ')
    string = string.replace(')', ' ) ')

    if language:
        words = mathwords.words_for_language(language)

        for phrase in words:
            escaped_phrase = phrase.replace(' ', escape)
            string = string.replace(phrase, escaped_phrase)

    tokens = string.split()

    for index, token in enumerate(tokens):
        tokens[index] = token.replace(escape, ' ')

    return tokens




def to_postfix(tokens):
    """
    Convert a list of evaluatable tokens to postfix format.
    """
    precedence = {
        '/': 4,
        '*': 4,
        '+': 3,
        '-': 3,
        '^': 2,
        '(': 1
    }

    postfix = []
    opstack = []

    for token in tokens:
        if is_int(token):
            postfix.append(int(token))
        elif is_float(token):
            postfix.append(float(token))
        elif token in mathwords.CONSTANTS:
            postfix.append(mathwords.CONSTANTS[token])
        elif is_unary(token):
            opstack.append(token)
        elif token == '(':
            opstack.append(token)
        elif token == ')':
            top_token = opstack.pop()
            while top_token != '(':
                postfix.append(top_token)
                top_token = opstack.pop()
        else:
            while (opstack != []) and (
                precedence[opstack[-1]] >= precedence[token]
            ):
                postfix.append(opstack.pop())
            opstack.append(token)

    while opstack != []:
        postfix.append(opstack.pop())

    return postfix




def evaluate_postfix(tokens):
    """
    Given a list of evaluatable tokens in postfix format,
    calculate a solution.
    """
    stack = []

    for token in tokens:
        total = None

        if is_int(token) or is_float(token) or is_constant(token):
            stack.append(token)
        elif is_unary(token):
            a = stack.pop()
            total = mathwords.UNARY_FUNCTIONS[token](a)
        elif len(stack):
            b = stack.pop()
            a = stack.pop()
            if token == '+':
                total = a + b
            elif token == '-':
                total = a - b
            elif token == '*':
                total = a * b
            elif token == '^':
                total = a ** b
            elif token == '/':
                if Decimal(str(b)) == 0:
                    total = 'undefined'
                else:
                    total = Decimal(str(a)) / Decimal(str(b))
            else:
                raise PostfixTokenEvaluationException(f'Unknown token {token}')

        if total is not None:
            stack.append(total)

    # If the stack is empty the tokens could not be evaluated
    if not stack:
        raise PostfixTokenEvaluationException(
            'The postfix expression resulted in an empty stack'
        )

    return stack.pop()

