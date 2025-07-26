# lexer.py

import ply.lex as lex

# 关键字列表
reserved = {
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'for': 'FOR',
    'in': 'IN',
    'print': 'PRINT',
    'def': 'DEF',  # --- NEW ---
    'return': 'RETURN',  # --- NEW ---
}

# 所有 Token 类型
tokens = [
    'NUMBER',       # 数字 包含INTEGER与FLOAT
    'STRING',       # 字符串字面量
    'PLUS',         # +
    'MINUS',        # -
    'TIMES',        # *
    'DIVIDE',       # /
    'ASSIGN',       # =
    'EQ',           # ==
    'NEQ',          # !=
    'LT',           # <
    'LTE',          # <=
    'GT',           # >
    'GTE',          # >=
    'LPAREN',       # (
    'RPAREN',       # )
    'COLON',        # :
    'COMMA',  # ,       --- NEW ---
    'IDENTIFIER',   # 标识符
    'NEWLINE',      # 逻辑换行符
    'INDENT',       # 缩进
    'DEDENT',       # 反缩进
] + list(reserved.values())

# 定义词法分析器的状态
states = (
    # 第一个参数是状态名，第二个参数 'exclusive' 或 'inclusive'
    # 'exclusive': 在此状态下，只有该状态的规则 (t_STATENAME_xxxx) 生效
    # 'inclusive': 在此状态下，该状态的规则和 INITIAL 状态的规则都可能生效
    ('string', 'exclusive'),
)

# --- INITIAL 状态规则 (默认状态) ---
# 为了清晰，所有在INITIAL状态下的规则都以 t_INITIAL_ 开头

t_INITIAL_PLUS = r'\+'
t_INITIAL_MINUS = r'-'
t_INITIAL_TIMES = r'\*'
t_INITIAL_DIVIDE = r'/'
t_INITIAL_ASSIGN = r'='
t_INITIAL_EQ = r'=='
t_INITIAL_NEQ = r'!='
t_INITIAL_LT = r'<'
t_INITIAL_LTE = r'<='
t_INITIAL_GT = r'>'
t_INITIAL_GTE = r'>='
t_INITIAL_LPAREN = r'\('
t_INITIAL_RPAREN = r'\)'
t_INITIAL_COLON = r':'
t_INITIAL_COMMA = r','   # --- NEW ---


# 忽略规则：行内的空格和制表符 (在 INITIAL 状态)
t_INITIAL_ignore = ' \t\r'

def t_INITIAL_NUMBER(t):
    # 这个正则的顺序很重要，更具体的（如带小数点的）应该能优先于纯整数。
    # PLY 会选择匹配最长前缀的。
    # "1.23" -> 被第一部分匹配
    # "1e5"  -> 被第二部分匹配
    # "123"  -> 被第三部分匹配
    r'((\d+\.\d*)|(\.\d+))([eE][-+]?\d+)? | \d+[eE][-+]?\d+ | \d+'
    original_text = t.value  # 保存原始匹配文本
    try:
        if '.' in original_text or 'e' in original_text.lower():
            t.value = float(original_text)
        else:
            t.value = int(original_text)
        # t.type 保持为 'NUMBER' (由函数名 t_INITIAL_NUMBER 推断)
        return t
    except ValueError:
        print(f"词法错误：无法将 '{original_text}' 转换为数字，行 {t.lexer.lineno}")
        t.lexer.skip(len(original_text))
        return None

def t_INITIAL_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t

# 规则：匹配字符串的开始 (在 INITIAL 状态)
def t_INITIAL_STRING_START(t):
    r'\"|\''  # 匹配一个双引号或一个单引号
    t.lexer.string_start_pos = t.lexpos       # 记录字符串字面量开始的原始位置
    t.lexer.string_start_line = t.lexer.lineno # 记录字符串开始的行号
    t.lexer.string_quote_char = t.value[0]    # 记录开始的引号类型 (" 或 ')
    t.lexer.string_buffer = []                # 用于存储字符串内容的缓冲区
    t.lexer.push_state('string')              # 进入 'string' 状态
    # 这个规则本身不返回Token，它只是状态转换和初始化的触发器

def t_INITIAL_ignore_COMMENT(t):
    r'\#.*'
    pass # 不返回任何值，PLY会忽略这个匹配


# --- 'string' 状态规则 ---
# 在此状态下，只有以 t_string_ 开头的规则生效

# 1. 匹配字符串中的转义序列
def t_string_ESCAPE(t):
    r'\\.'  # 匹配一个反斜杠后跟任何单个字符
    escaped_char = t.value[1]
    if escaped_char == 'n':
        t.lexer.string_buffer.append('\n')
    elif escaped_char == 't':
        t.lexer.string_buffer.append('\t')
    elif escaped_char == '"':
        t.lexer.string_buffer.append('"')
    elif escaped_char == "'":
        t.lexer.string_buffer.append("'")
    elif escaped_char == '\\':
        t.lexer.string_buffer.append('\\')
    else:
        # 对于未明确处理的转义序列，保留反斜杠和其后的字符
        # 例如，Python中 "\c" 在字符串字面量中会是 "\\c"
        # 或者，对于简单编译器，可以直接报错或仅保留原样字符
        t.lexer.string_buffer.append('\\')
        t.lexer.string_buffer.append(escaped_char)

# 2. 匹配字符串的结束引号
def t_string_END(t):
    # 这个正则表达式需要动态地基于 t.lexer.string_quote_char
    # PLY的t_规则不支持直接使用lexer状态来构建正则表达式字符串。
    # 所以，我们将匹配任何引号，然后在Python代码中检查它是否是正确的结束引号。
    r'\"|\''
    if t.value == t.lexer.string_quote_char:  # 如果是匹配的结束引号
        t.value = "".join(t.lexer.string_buffer)
        t.type = "STRING"
        # STRING token的行号和位置应为其开始的位置
        t.lineno = t.lexer.string_start_line
        t.lexpos = t.lexer.string_start_pos
        t.lexer.pop_state()  # 返回到 INITIAL 状态
        return t
    else:  # 引号不匹配 (例如 "string started with ' but found " )
           # 这种情况是字符串内容的一部分
        t.lexer.string_buffer.append(t.value)

# 3. 在string状态下，遇到换行符 -> 错误：未闭合的字符串
def t_string_NEWLINE_UNCLOSED(t):
    r'\n+'  # 匹配一个或多个换行符
    print(f"词法错误：在行 {t.lexer.string_start_line} 位置 {t.lexer.string_start_pos} 开始的字符串未闭合，在行 {t.lexer.lineno} 遇到换行。")
    t.lexer.lineno += len(t.value) -1 # t.lexer.lineno在规则执行前已基于\n更新了一次，所以这里减1再加len
                                     # 或者直接: t.lexer.lineno += len(t.value) (如果PLY的\n计数已发生)
                                     # PLY文档说: "When a newline is encountered, the t_lexer.lineno attribute is automatically incremented"
                                     # 所以我们只需要处理多个换行的情况，如果len(t.value) > 1
    if len(t.value) > 1:
         t.lexer.lineno += (len(t.value) -1) # 如果匹配了多个\n

    t.lexer.pop_state()  # 返回INITIAL状态，放弃当前字符串
    # 此规则不返回Token，错误已打印

# 4. 在string状态下，捕获所有其他单个字符作为字符串内容
# 这个规则的优先级应该低于ESCAPE, END, 和 NEWLINE_UNCLOSED。
# PLY按规则定义的顺序和正则表达式的长度来决定优先级。
# 把这个规则放在最后，或者确保它的正则表达式比其他的更“通用”但不会意外捕获。
def t_string_CONTENT_CHAR(t):
    r'[^\\\'\"\n]+'  # 匹配任何非 (\, ', ", newline) 的字符序列
                     # 确保不会贪婪地吃到应该由其他规则处理的字符
    t.lexer.string_buffer.append(t.value)


# 5. 在string状态下，如果遇到EOF，说明字符串未闭合
def t_string_eof(t): # 特殊的 eof 规则，只在当前状态为 'string' 时PLY会尝试调用
    print(f"词法错误：在行 {t.lexer.string_start_line} 位置 {t.lexer.string_start_pos} 开始的字符串未在文件结束前闭合。")
    # PLY 在 EOF 时会自动尝试 pop state (如果 lexer 对象有 push_state 调用历史)
    # 但明确 pop_state() 也是好的
    # t.lexer.pop_state() # 不需要，PLY会自动处理，或者如果需要确保，可以加
    # 这个eof规则不返回token，只是报告错误。PLY的lexer在EOF时最终会返回None。
    return None # 必须返回None或一个Token，或者不返回让PLY处理

# string 状态的错误处理 (如果以上规则都未匹配)
def t_string_error(t):
    print(f"词法内部错误：在解析字符串时遇到意外字符 '{t.value[0]}' 在行 {t.lexer.lineno} 位置 {t.lexpos}。这通常不应发生。")
    t.lexer.string_buffer.append(t.value[0]) # 尝试包含错误字符并继续
    t.lexer.skip(1)


# --- 处理缩进和换行的规则 (在 INITIAL 状态) ---
def _new_logical_token(type, lineno, lexpos):
    tok = lex.LexToken()
    tok.type = type
    tok.value = None
    tok.lineno = lineno
    tok.lexpos = lexpos
    return tok

def t_INITIAL_ignore_NEWLINE_INDENT_HANDLER(t):
    r'\n[ \t]*'
    lexer = t.lexer
    lexer.lineno += 1  # 手动增加行号，因为我们匹配了整个换行和缩进

    # 计算当前物理缩进
    current_physical_indent = 0
    for char_in_indent in t.value[1:]:  # t.value[0] is '\n'
        if char_in_indent == ' ':
            current_physical_indent += 1
        elif char_in_indent == '\t':
            current_physical_indent = (current_physical_indent // lexer.tabsize + 1) * lexer.tabsize

    # 首先总是生成NEWLINE标记
    lexer.pending_tokens.append(_new_logical_token('NEWLINE', lexer.lineno, t.lexpos))

    # 处理缩进变化
    if current_physical_indent > lexer.indent_stack[-1]:
        # 增加缩进级别并生成INDENT标记
        lexer.indent_stack.append(current_physical_indent)
        lexer.pending_tokens.append(_new_logical_token('INDENT', lexer.lineno, t.lexpos))
    elif current_physical_indent < lexer.indent_stack[-1]:
        # 减少缩进级别，生成足够数量的DEDENT标记
        while current_physical_indent < lexer.indent_stack[-1]:
            lexer.indent_stack.pop()
            lexer.pending_tokens.append(_new_logical_token('DEDENT', lexer.lineno, t.lexpos))
        # 检查是否匹配
        if current_physical_indent != lexer.indent_stack[-1]:
            raise SyntaxError(f"缩进错误：行 {lexer.lineno} 的缩进级别 {current_physical_indent} 与已知的缩进栈不匹配。栈: {lexer.indent_stack}")

    # 空行（只有换行和空格）不产生任何标记（除了NEWLINE）
    # 这里不需要额外处理，因为上面的逻辑已经处理了所有情况

# INITIAL 状态的通用错误处理规则
def t_INITIAL_error(t):
    # 需求2：处理孤立的右引号 print(hello")
    # 如果一个孤立的引号没有被 t_INITIAL_STRING_START 消费（因为它后面没有构成合法字符串的模式，
    # 或者它本身是想作为结束引号但没有匹配的开始引号），它会进入这里。
    if t.value[0] == '"' or t.value[0] == "'":
        print(f"词法错误：在行 {t.lexer.lineno} 位置 {t.lexpos} 遇到孤立的或意外的引号 '{t.value[0]}'")
    else:
        print(f"词法错误：在行 {t.lexer.lineno}，位置 {t.lexpos} 遇到非法字符 '{t.value[0]}'")
    t.lexer.skip(1)


# --- LexerWrapper 和其他辅助代码 ---
class LexerWrapper:
    def __init__(self, tabsize=4):
        self.lexer = lex.lex(errorlog=lex.NullLogger()) # PLY会自动找到states元组
        self.lexer.tabsize = tabsize
        self.lexer.indent_stack = [0]
        self.lexer.pending_tokens = []
        self.eof_dedents_done = False
        # string状态用的变量会被动态添加到lexer实例中:
        # self.lexer.string_start_pos, self.lexer.string_start_line,
        # self.lexer.string_quote_char, self.lexer.string_buffer

    def input(self, data):
        # 确保输入数据末尾有换行符，有助于触发最后的DEDENT和NEWLINE
        if data and not data.endswith('\n'):
            data += '\n'
        elif not data: # 空文件也给一个换行
            data = '\n'

        self.lexer.input(data)
        # 重置自定义状态
        self.lexer.indent_stack = [0]
        self.lexer.pending_tokens = []
        self.eof_dedents_done = False
        # 确保lexer状态回到INITIAL，以防上次解析因错误而停在 'string' 状态
        # PLY的lexer.input()通常会重置状态，但为了保险
        while hasattr(self.lexer, 'current_state') and self.lexer.current_state() != 'INITIAL':
             if self.lexer.lexstatestack: # 确保栈非空
                self.lexer.pop_state()
             else: # 如果栈空但状态不是INITIAL (不太可能发生)
                break


    def token(self):
        # 1. 优先处理 pending_tokens (INDENT, DEDENT, NEWLINE)
        if self.lexer.pending_tokens:
            return self.lexer.pending_tokens.pop(0)

        # 2. 如果已处理完EOF的DEDENT且队列空，则结束
        if self.eof_dedents_done and not self.lexer.pending_tokens:
            return None

        # 3. 获取下一个原始Token
        raw_tok = self.lexer.token() # 这会调用PLY的lexer.token()，它会处理状态

        # 4. 处理文件末尾 (EOF)
        if raw_tok is None:
            # 如果在string状态下遇到EOF，t_string_eof应该已经被调用并报告错误
            # 这里检查是否还在string状态（理论上不应该，t_string_eof会处理）
            if hasattr(self.lexer, 'current_state') and self.lexer.current_state() == 'string':
                # 这是个备用逻辑或额外检查
                # print(f"词法错误(EOF备用)：行 {self.lexer.string_start_line} 字符串未闭合。")
                if self.lexer.lexstatestack: self.lexer.pop_state()

            # 处理EOF时的DEDENTs (如果不在string状态)
            if not self.eof_dedents_done and (not hasattr(self.lexer, 'current_state') or self.lexer.current_state() == 'INITIAL'):
                while len(self.lexer.indent_stack) > 1:
                    self.lexer.indent_stack.pop()
                    # EOF的DEDENT位置可能是最后一个字符之后，或者最后一个有效token的位置
                    dedent_pos = getattr(self.lexer, 'lexpos', 0)
                    if hasattr(self.lexer, 'last_tok_pos'): # 如果我们记录了最后一个token的位置
                        dedent_pos = self.lexer.last_tok_pos

                    self.lexer.pending_tokens.append(
                        _new_logical_token('DEDENT', self.lexer.lineno, dedent_pos)
                    )
                self.eof_dedents_done = True

                if self.lexer.pending_tokens: # 如果因EOF产生了DEDENT
                    return self.lexer.pending_tokens.pop(0)
            return None # 真正到达文件结束

        # 记录最后一个成功获取的token的位置，可用于EOF DEDENT的定位
        self.lexer.last_tok_pos = raw_tok.lexpos + len(str(raw_tok.value)) if raw_tok else getattr(self.lexer, 'lexpos', 0)

        # 5. 如果原始token不是None，并且pending_tokens因换行处理而有内容
        if self.lexer.pending_tokens:
            self.lexer.pending_tokens.append(raw_tok) # raw_tok排在INDENT/DEDENT/NEWLINE之后
            return self.lexer.pending_tokens.pop(0)
        else:
            return raw_tok # 直接返回原始token

_global_lexer_instance = None
def get_lexer_instance(tabsize=4):
    # 为了确保每次测试或编译都是干净的，最好每次都创建一个新的 LexerWrapper 实例
    # global _global_lexer_instance
    # if _global_lexer_instance is None:
    #    _global_lexer_instance = LexerWrapper(tabsize=tabsize)
    # return _global_lexer_instance
    return LexerWrapper(tabsize=tabsize) # 总是创建新的实例


# --- 测试代码 ---
if __name__ == '__main__':
#     test_cases = [
#         ("正常字符串", 'print("hello world")\nx = \'single quote\''),
#         ("需求1: 缺少右双引号后有换行", 'print("hello world\nprint("next line")'),
#         ("需求1: 缺少右单引号至EOF", "s = 'abc def"),
#         ("需求1: 字符串正确跨行(Python不支持直接回车换行，除非用三引号或行尾\\)",
#          's = "line one"\n#   line two"  <-- 这会被当成两个语句\nprint(s)'), # 这个用例需要调整理解
#         ("调整后的跨行理解：字符串在同一行，但逻辑上想表达未闭合后遇到新内容",
#          's = "this is an unclosed string then code comes after\nval = 10'),
#         ("需求3: 正常闭合 print(\"hello\")", 'print("hello")'),
#         ("需求2: 缺少左引号 (孤立右引号)", 'print(hello")'), # `hello`是IDENTIFIER, `"`是错误
#         ("需求2: 更多孤立引号", 'a = 10" + b"'), # 10是NUMBER, `"`是错误, +是PLUS, b是IDENTIFIER, `"`是错误
#         ("字符串内有另一种引号", 'print("string with \'single\' quote")\nprint(\'string with "double" quote\')'),
#         ("空字符串", 'print("")\nprint(\'\')'),
#         ("转义字符", 'print("esc: \\n \\t \\\\ \\" \\\'")'),
#         ("复杂嵌套和未闭合字符串", """
# if x > 10:
#     name = "User"
#     print("Hello, " + name) # 假设我们以后支持字符串拼接
#     if y < 5:
#         message = 'Alert: value is # 未闭合
#         print(message) # message 在上一行因未闭合字符串而出错
# print("Final") # 这个print可能不会被正确解析如果前面有严重词法错误
# """),
#         ("包含中文的正常字符串", 'print("你好，世界！")'),
#         ("包含中文的未闭合字符串", 'print("你好，世'),
#         ("单引号未闭合，后跟代码", "title = 'My Story\nnext_var = 1"),
#         ("连续多个字符串", 'a = "first" "second" # Python中这是合法的字符串拼接，我们这里会是两个STRING token\nprint(a)'), # 在我们的实现中，如果中间没有操作符，语法分析会报错
#     ]
    test_cases=[("func",'''
a=1
b=1
def add(x,y):
    return x+y
c=a+b
print(c)
    ''')]
    for name, source_code in test_cases:
        print(f"\n--- 测试用例: {name} ---")
        print(f"源代码:\n```python\n{source_code}\n```")
        print("--- 生成的 Tokens 和错误 ---")

        # 每次测试都获取一个新的lexer实例
        my_lexer = get_lexer_instance(tabsize=4)
        my_lexer.input(source_code)

        token_count = 0
        while True:
            tok = my_lexer.token()
            if not tok:
                break
            token_count +=1
            value_repr = repr(tok.value) if tok.type == 'STRING' else str(tok.value)
            print(f"类型: {tok.type:<10s} 值: {value_repr:<40s} 行号: {tok.lineno:<3d} 位置: {tok.lexpos:<4d}")

        if token_count == 0 and source_code.strip() and not "错误" in name: # 粗略判断
             # 检查是否有打印错误，因为错误信息直接打印到控制台
             # 这个判断逻辑可以更完善
            pass # 错误信息会直接打印，这里不再重复提示
        elif token_count == 0 and not source_code.strip():
            print("(符合预期：空有效源码通常不生成业务Token)")
        print("-" * 40)

    print("\n--- 所有测试完成 ---")