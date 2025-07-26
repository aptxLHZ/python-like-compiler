# symbol_table.py

class Symbol:
    """符号表中的条目"""

    def __init__(self, name, sym_type=None, scope_level=0, value=None, lineno=None, lexpos=None):
        self.name = name
        self.sym_type = sym_type  # 例如 "INTEGER", "FLOAT", "STRING", "VARIABLE", "FUNCTION" (未来)
        # 对于动态类型，可能只记录 'ASSIGNED' 或具体值的类型
        self.scope_level = scope_level  # 0 表示全局
        self.value = value  # 如果是常量，可以存储其值；变量在运行时才有值
        self.lineno = lineno  # 定义时的行号
        self.lexpos = lexpos  # 定义时的位置
        # 未来可以添加：内存地址/偏移量等

    def __repr__(self):
        return (f"Symbol(name='{self.name}', type='{self.sym_type}', "
                f"scope={self.scope_level}, value={repr(self.value)})")
        # return (f"Symbol(name='{self.name}', type='{self.sym_type}', "
        #         f"scope={self.scope_level}, value={repr(self.value)}, "
        #         f"line={self.lineno}, pos={self.lexpos})")


class SymbolTable:
    """符号表管理器"""

    def __init__(self):
        self.scopes = [{}]  # 作用域栈，每个元素是一个作用域字典 {'name': Symbol}
        self.current_scope_level = 0  # 当前作用域级别，0为全局

    def define(self, name, sym_type=None, value=None, lineno=None, lexpos=None):
        current_scope = self.scopes[-1]  # 当前作用域
        symbol = Symbol(name, sym_type, self.current_scope_level, value, lineno, lexpos)
        current_scope[name] = symbol
        print(f"符号定义/更新: {symbol}")  # 调试信息
        return symbol



    # --- MODIFICATION START ---
    def lookup(self, name, current_scope_only=False):
        """
        在符号表中查找一个符号。
        :param name: 要查找的符号名称。
        :param current_scope_only: 如果为True，则只在当前作用域中查找。
        :return: 找到的 Symbol 对象或 None。
        """
        if current_scope_only:
            # 只在当前作用域 (栈顶) 查找
            scope = self.scopes[-1]
            if name in scope:
                return scope[name]
        else:
            # 从当前作用域向上查找所有作用域
            for i in range(len(self.scopes) - 1, -1, -1):
                scope = self.scopes[i]
                if name in scope:
                    return scope[name]

        return None  # 未找到
    # --- MODIFICATION END ---

    def enter_scope(self):
        self.current_scope_level += 1
        self.scopes.append({})
        print(f"进入作用域 {self.current_scope_level}")

    def exit_scope(self):
        if len(self.scopes) > 1:  # 防止pop掉全局作用域
            print(f"退出作用域 {self.current_scope_level}, 符号: {self.scopes[-1]}")
            self.scopes.pop()
            self.current_scope_level -= 1
        else:
            print("警告：试图退出全局作用域。")

    def get_current_scope_level(self):
        return self.current_scope_level

    def __repr__(self):
        # 自定义一个漂亮的 __repr__
        s = "SymbolTable(\n"
        for i, scope in enumerate(self.scopes):
            s += f"  Scope {i} (level {self.scopes[i-len(self.scopes)].current_scope_level if i>0 else 0}): {{\n" # A bit tricky to get level right
            if not scope:
                s += "    (empty)\n"
            else:
                for name, symbol in scope.items():
                    s += f"    '{name}': {symbol}\n"
            s += "  }\n"
        s += ")"
        return s
    # 一个更简单的实现
    def __str__(self):
        # 使用 __str__ 来提供漂亮打印，保留 __repr__ 为单行调试信息
        output = "SymbolTable:\n"
        output += "==============\n"
        for i, scope in reversed(list(enumerate(self.scopes))):
            output += f"--- Scope (level {i}) ---\n"
            if not scope:
                output += "  (empty)\n"
            else:
                for name, symbol in scope.items():
                    output += f"  {name:<15} : {symbol}\n"
        output += "==============\n"
        return output






# --- 简单测试 ---
if __name__ == '__main__':
    st = SymbolTable()
    st.define("x", sym_type="INTEGER", value=10, lineno=1, lexpos=0)
    st.define("message", sym_type="STRING", value="hello", lineno=2, lexpos=0)

    print(st.lookup("x"))
    print(st.lookup("message"))
    print(st.lookup("y"))  # None

    st.define("x", sym_type="STRING", value="new_x", lineno=3, lexpos=0)  # 重新赋值
    print(st.lookup("x"))

    print(st)