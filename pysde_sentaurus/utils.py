import re

# precedence level of supported operators.
PRECEDENCE = {
    '^': 4, # highest precedence level
    '*': 3,
    '/': 3,
    '+': 2,
    '-': 2,
    '=': 2,
    '>': 2,
    '<': 2,
    '(': 1,
}

def infix_to_postfix(expr):
    """ Converts to reverse polish notation.

    Taken from https://www.educative.io/answers/how-to-convert-infix-expressions-to-postfix-expressions-in-python

    :param expr: string with the expression in regular order.
    """

    tokens = re.findall(r"(\b\w*[\.]?\w+\b|[\(\)\^\+\*\-\/\=\>\<])", expr)
    stack = []
    postfix = []
    
    for token in tokens:
        # If the token is an operand, then do not push it to stack. 
        # Instead, pass it to the output.
        if re.match(r'^[A-Za-z0-9_.]+$', token):
            postfix.append(token)
    
        # If your current token is a right parenthesis
        # push it on to the stack
        elif token == '(':
            stack.append(token)

        # If your current token is a right parenthesis,
        # pop the stack until after the first left parenthesis.
        # Output all the symbols except the parentheses.
        elif token == ')':
            top = stack.pop()
            while top != '(':
                postfix.append(top)
                top = stack.pop()

        # Before you can push the operator onto the stack, 
        # you have to pop the stack until you find an operator
        # with a lower priority than the current operator.
        # The popped stack elements are written to output.
        else:
            while stack and (PRECEDENCE[stack[-1]] >= PRECEDENCE[token]):
                postfix.append(stack.pop())
            stack.append(token)

    # After the entire expression is scanned, 
    # pop the rest of the stack 
    # and write the operators in the stack to the output.
    while stack:
        postfix.append(stack.pop())
    return ' '.join(postfix)


def infix_to_prefix(expr):

    reverse_expr =''
    for c in expr[::-1]:
        if c == '(':
            reverse_expr += ")"
        elif c == ')':
            reverse_expr += "("
        else:
            reverse_expr += c

    reverse_postfix = infix_to_postfix(reverse_expr)

    return reverse_postfix[::-1]


        

if __name__ == "__main__":

    # Some tests
    expressions = ['4*2+5*(2+1)/2', '4^2+5*(2+1)/2',  'A*(B+30)/D', 'a = b', '(l_input * 3.2e4 / 2)']


    for expr in expressions:
        print(infix_to_postfix(expr))
        print(infix_to_prefix(expr))