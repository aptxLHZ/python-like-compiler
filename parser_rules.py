# parser_rules.py
# PLY  LALR(1)文法

import ply.yacc as yacc
from lexer import tokens
from ast_nodes import (
    ProgramNode, AssignmentNode, PrintNode, IfNode, WhileNode, ForNode,
    BlockNode, BinaryOpNode, NumberNode, StringNode, IdentifierNode,
    FunctionDefNode, FunctionCallNode, ReturnNode  # --- MODIFIED ---
)
# --- 操作符优先级和结合性 ---
precedence = (
    # 'NEWLINE' 一般不参与运算优先级，我们不在这里定义它，除非有非常特殊的需求
    ('left', 'COMMA'),  # --- NEW ---
    ('left', 'EQ', 'NEQ', 'LT', 'LTE', 'GT', 'GTE'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)
# --- 文法规则 ---
def p_program(p):
    """
    program : optional_newlines statement_sequence
    """
    # statement_sequence 返回语句列表
    p[0] = ProgramNode(p[2])
def p_optional_newlines(p):
    """
    optional_newlines : optional_newlines NEWLINE
                      | empty
    """
    # 这个规则只是为了消费掉程序开头可能存在的空行
    # 它不产生任何值，或者说它的值不重要
    pass
def p_statement_sequence(p):
    # 允许完全空的程序（只有注释或空白）
    """
    statement_sequence : statement_plus_optional_newlines
                       | empty
    """
    if p[1] is None:  # empty 规则
        p[0] = []
    else:
        p[0] = p[1]  # p[1] is a list from statement_plus_optional_newlines
def p_statement_plus_optional_newlines(p):
    """
    statement_plus_optional_newlines : statement_plus_optional_newlines statement_with_trailing_newlines
                                     | statement_with_trailing_newlines
    """
    if len(p) == 2:  # statement_with_trailing_newlines
        if p[1] is not None:  # p[1] is a single statement
            p[0] = [p[1]]
        else:  # p[1] might be None if statement was empty and only newlines followed
            p[0] = []
    else:  # statement_plus_optional_newlines statement_with_trailing_newlines
        if p[2] is not None:  # p[2] is a single statement
            p[1].append(p[2])
        p[0] = p[1]
def p_statement_with_trailing_newlines(p):
    #单独的空行，被statement_plus_optional_newlines忽略
    """
    statement_with_trailing_newlines : statement optional_newlines_after_statement
                                     | NEWLINE
    """
    if p.slice[1].type == 'NEWLINE':  # 如果第一个token是NEWLINE，说明这是个空行
        p[0] = None  # 返回None，让上一层规则忽略它
    else:  # statement optional_newlines_after_statement
        p[0] = p[1]  # 返回 statement 节点
def p_optional_newlines_after_statement(p):
    """
    optional_newlines_after_statement : optional_newlines_after_statement NEWLINE
                                      | empty
    """
    # 消费掉语句后的所有NEWLINE，直到下一个实际内容或EOF
    pass
def p_statement(p):
    """
    statement : assignment_statement
              | print_statement
              | if_statement
              | while_statement
              | for_statement
               | function_def_statement
              | return_statement
              | expression_statement
    """
    # 后续添加pass功能  pass_statement
    p[0] = p[1]
    if p[0] is not None:
        if not hasattr(p[0], 'lineno') or p[0].lineno is None:
            try:
                first_symbol = p.slice[1]
                if hasattr(first_symbol, 'lineno'):
                    p[0].lineno = first_symbol.lineno
                    p[0].lexpos = first_symbol.lexpos
            except (IndexError, AttributeError):
                pass
def p_assignment_statement(p):
    """
    assignment_statement : IDENTIFIER ASSIGN expression
    """
    identifier_node = IdentifierNode(p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))
    p[0] = AssignmentNode(identifier_node, p[3], lineno=p.lineno(1), lexpos=p.lexpos(1))
def p_print_statement(p):
    """
    print_statement : PRINT LPAREN expression RPAREN
    """
    p[0] = PrintNode(p[3], lineno=p.lineno(1), lexpos=p.lexpos(1))
def p_expression_statement(p):
    """
    expression_statement : expression
    """
    p[0] = p[1]
def p_function_def_statement(p):
    """
    function_def_statement : DEF IDENTIFIER LPAREN parameter_list RPAREN COLON suite
    """
    name_node = IdentifierNode(p[2], lineno=p.lineno(2), lexpos=p.lexpos(2))
    p[0] = FunctionDefNode(name_node, p[4], p[7], lineno=p.lineno(1), lexpos=p.lexpos(1))
def p_parameter_list(p):
    """
    parameter_list : param_items
                   | empty
    """
    p[0] = p[1] if p[1] is not None else []
def p_param_items(p):
    """
    param_items : param_items COMMA IDENTIFIER
                | IDENTIFIER
    """
    if len(p) == 2: # IDENTIFIER
        p[0] = [IdentifierNode(p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))]
    else: # param_items COMMA IDENTIFIER
        p[1].append(IdentifierNode(p[3], lineno=p.lineno(3), lexpos=p.lexpos(3)))
        p[0] = p[1]
def p_return_statement(p):
    """
    return_statement : RETURN expression
    """
    p[0] = ReturnNode(p[2], lineno=p.lineno(1), lexpos=p.lexpos(1))
def p_if_statement(p):
    """
    if_statement : IF condition COLON suite
                 | IF condition COLON suite ELSE COLON suite
    """
    condition = p[2]
    then_suite = p[4]
    else_suite = None
    if len(p) == 8:
        else_suite = p[7]
    p[0] = IfNode(condition, then_suite, else_suite, lineno=p.lineno(1), lexpos=p.lexpos(1))
def p_while_statement(p):
    """
    while_statement : WHILE condition COLON suite
    """
    p[0] = WhileNode(p[2], p[4], lineno=p.lineno(1), lexpos=p.lexpos(1))
def p_for_statement(p):
    """
    for_statement : FOR IDENTIFIER IN expression COLON suite
    """
    loop_var = IdentifierNode(p[2], lineno=p.lineno(2), lexpos=p.lexpos(2))
    iterable_expr = p[4]
    body_suite = p[6]
    p[0] = ForNode(loop_var, iterable_expr, body_suite, lineno=p.lineno(1), lexpos=p.lexpos(1))
# def p_pass_statement(p):
#     """
#     pass_statement : PASS
#     """
#     p[0] = None  # 或者创建一个 PassNode 如果你有这样的 AST 节点
def p_suite(p):
    """
    suite : NEWLINE INDENT statement_sequence DEDENT
    """
    # statement_sequence 现在返回一个列表 (可能为空)
    p[0] = BlockNode(p[3], lineno=p.lineno(1), lexpos=p.lexpos(1))
def p_condition(p):
    """
    condition : expression
    """
    p[0] = p[1]
def p_expression_binop(p):
    """
    expression : expression PLUS expression
               | expression MINUS expression
               | expression TIMES expression
               | expression DIVIDE expression
               | expression EQ expression
               | expression NEQ expression
               | expression LT expression
               | expression LTE expression
               | expression GT expression
               | expression GTE expression
    """
    op_token = p.slice[2]
    node_lineno = p[1].lineno if hasattr(p[1], 'lineno') and p[1].lineno is not None else op_token.lineno
    node_lexpos = p[1].lexpos if hasattr(p[1], 'lexpos') and p[1].lexpos is not None else op_token.lexpos
    p[0] = BinaryOpNode(p[1], op_token, p[3], lineno=node_lineno, lexpos=node_lexpos)
def p_expression_group(p):
    """
    expression : LPAREN expression RPAREN
    """
    p[0] = p[2]
    if hasattr(p[0], 'lineno') and p[0].lineno is None:
        p[0].lineno = p.lineno(1)
        p[0].lexpos = p.lexpos(1)
def p_expression_identifier(p):
    """
    expression : IDENTIFIER
    """
    p[0] = IdentifierNode(p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))
def p_expression_number(p):
    """
    expression : NUMBER
    """
    p[0] = NumberNode(p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))
def p_expression_string(p):
    """
    expression : STRING
    """
    p[0] = StringNode(p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))
def p_expression_factor(p):
    """
    expression : factor
    """
    p[0] = p[1]
def p_factor(p):
    """
    factor : IDENTIFIER
           | NUMBER
           | STRING
           | function_call
    """
    # p[1] is the value of the matched token or the result from another rule.
    # We need to create nodes for raw tokens.

    # 检查 p.slice[1].type 是更健壮的方式
    token_type = p.slice[1].type

    if token_type == 'IDENTIFIER':
        p[0] = IdentifierNode(p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))
    elif token_type == 'NUMBER':
        p[0] = NumberNode(p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))
    elif token_type == 'STRING':
        p[0] = StringNode(p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))
    else:  # 已经是 Node 了 (来自 function_call)
        p[0] = p[1]
def p_function_call(p):
    """
    function_call : IDENTIFIER LPAREN argument_list RPAREN
    """
    name_node = IdentifierNode(p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))
    p[0] = FunctionCallNode(name_node, p[3], lineno=p.lineno(1), lexpos=p.lexpos(1))
def p_argument_list(p):
    """
    argument_list : arg_items
                  | empty
    """
    p[0] = p[1] if p[1] is not None else []
def p_arg_items(p):
    """
    arg_items : arg_items COMMA expression
              | expression
    """
    if len(p) == 2: # expression
        p[0] = [p[1]]
    else: # arg_items COMMA expression
        p[1].append(p[3])
        p[0] = p[1]
def p_empty(p):
    """
    empty :
    """
    p[0] = None
def p_error(p):
    if p:
        print(f"语法错误：在 Token '{p.type}' (值: '{p.value}') 附近，行 {p.lineno}, 位置 {p.lexpos}")
    else:
        print("语法错误：在输入的末尾。可能缺少了某些部分或有未闭合的块。")




# --- 构建解析器 ---
_parser_instance = None


def get_parser_instance(debug=False, outputdir=None, **kwargs):
    global _parser_instance
    # if _parser_instance is None or debug or outputdir:
    _parser_instance = yacc.yacc(debug=debug, outputdir=outputdir, write_tables=True, **kwargs)
    # write_tables=True (默认) 会生成 parsetab.py
    return _parser_instance

def pretty_print_ast(node, indent=0):
    indent_str = ' ' * indent
    if isinstance(node, list):
        print(f"{indent_str}[")
        for item in node:
            pretty_print_ast(item, indent+4)
        print(f"{indent_str}]")
    elif hasattr(node, '__dict__'):
        print(f"{indent_str}{type(node).__name__}(")
        for k, v in node.__dict__.items():
            print(f"{indent_str}    {k}=", end='')
            pretty_print_ast(v, indent+8)
        print(f"{indent_str})")
    else:
        print(f"{indent_str}{repr(node)}")



# --- 测试代码 ---
if __name__ == '__main__':
    from lexer import get_lexer_instance

    test_source_codes = [
        # ... (保留之前的测试用例) ...
        ("简单赋值和打印", """
print(10)
x = 20 + 5
y = "hello"
print(x)
print(y)
"""),
        ("If语句", """
a = 10
b = 5
if a > b:
    print("a is greater")
    c = a - b
else:
    print("b is greater or equal")
    c = b - a
print(c)
"""),
        ("While语句", """
count = 0
while count < 3:
    print(count)
    count = count + 1
print("done")
"""),
        ("For语句", """
items_list = "placeholder"
for item in items_list:
    print(item)
    if item == 2:
        print("Found two")
"""),
        ("嵌套结构和空行", """
x = 1
if x == 1:

    print("x is one")

    y = 2
    if y == 2:
        print("y is two")

    print("still in x block")


print("end of program")
"""),
        ("表达式语句", "10 + 20\n\"a string\""),
        ("空程序", ""),
        ("只有注释和空行", """
# comment 1

# comment 2
"""),
        ("语法错误测试: 缺少冒号", "if a > b print(a)"),
        ("语法错误测试: 错误缩进 (这个更像是词法/语法交互问题)", """
if a:
print(1)
print(2)
"""),
        ("语法错误测试: 未预期的Token", "x = 10 + * 5"),
        ("多重空行", """
a = 1


b = 2
print(a+b)
"""),
        ("程序开头有空行", """

print("hello")
""")
    ]

    my_lexer_wrapper = get_lexer_instance()
    # 在第一次运行时，如果遇到构建错误，尝试删除 parsetab.py 和 parser.out (如果存在)
    # 然后开启 debug=True 看看冲突信息
    my_parser = get_parser_instance(debug=False)  # debug=True 会打印大量信息

    for name, source in test_source_codes:
        print(f"\n--- 测试: {name} ---")
        # print(f"源:\n{source}")
        print("--- AST ---")
        ast_tree = my_parser.parse(input=source, lexer=my_lexer_wrapper)

        if ast_tree:
            print(repr(ast_tree))
            pretty_print_ast(ast_tree, indent=0)
        else:
            if not source.strip():
                print("(空程序或只有注释，AST可能为 ProgramNode([]))")
            else:
                print("AST 生成失败或为 None (错误信息应已显示)")
        print("-" * 40)