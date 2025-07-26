# semantic_analyzer.py

import types # 需要导入 types

from ast_nodes import (
    ProgramNode, AssignmentNode, PrintNode, IfNode, WhileNode, ForNode,
    BlockNode, BinaryOpNode, NumberNode, StringNode, IdentifierNode,
    FunctionDefNode, FunctionCallNode, ReturnNode # --- NEW ---
)
from symbol_table import SymbolTable, Symbol  # 确保 Symbol 也被导入


class SemanticError(Exception):
    """自定义语义错误异常"""

    def __init__(self, message, lineno=None, lexpos=None):
        super().__init__(message)
        self.lineno = lineno
        self.lexpos = lexpos
        self.message = message

    def __str__(self):
        if self.lineno is not None and self.lexpos is not None:
            return f"语义错误 (行 {self.lineno}, 位置 {self.lexpos}): {self.message}"
        elif self.lineno is not None:
            return f"语义错误 (行 {self.lineno}): {self.message}"
        return f"语义错误: {self.message}"


class SemanticAnalyzer:
    """语义分析器，遍历AST并进行检查"""

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.current_function = None # 跟踪当前函数以进行返回类型检查等

    def visit(self, node):
        method_name = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        for attr, value in node.__dict__.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, node):
                        self.visit(item)
            elif isinstance(value, node):
                self.visit(value)

    def analyze(self, ast_root):
        if not isinstance(ast_root, ProgramNode):
            raise TypeError("分析的根节点必须是 ProgramNode")
        print("--- 开始语义分析 ---")
        try:
            self.visit(ast_root)
            print("语义分析成功完成。")
            # print("最终符号表:", self.symbol_table) # 调试
        except SemanticError as e:
            print(e)  # 打印自定义的语义错误
            # 可以选择在这里重新抛出异常，或者让主程序知道发生了错误
            raise  # 重新抛出，让主程序捕获
        except Exception as e:
            print(f"语义分析过程中发生意外错误: {e}")
            raise

    # --- AST节点访问方法 ---

    def visit_ProgramNode(self, node: ProgramNode):
        # self.symbol_table.enter_scope() # 进入全局作用域（如果SymbolTable设计为栈式）
        for statement in node.statements:
            if statement:  # 确保语句不是None (例如由空的terminated_statement产生)
                self.visit(statement)
        # self.symbol_table.exit_scope() # 退出全局作用域

    def visit_BlockNode(self, node: BlockNode):
        # BlockNode 本身不管理作用域，而是由调用它的节点（如 FunctionDefNode）来管理。
        for statement in node.statements:
            if statement:
                self.visit(statement)

    def visit_AssignmentNode(self, node: AssignmentNode):
        # 1. 分析右侧表达式，并尝试获取其类型
        #    对于我们的简单实现，我们可能不进行复杂的类型推断，
        #    而是假设表达式是合法的，或者只做非常基本的类型标记。
        rhs_type = self.visit(node.expression)  # visit方法应该返回推断的类型或一个标记

        # 2. 获取左侧标识符名称
        var_name = node.identifier.name

        # 3. 在符号表中定义/更新变量
        #    我们可以将 rhs_type 存储为变量的类型
        #    或者，如果 rhs_type 是一个具体的值（如数字或字符串常量），也可以存值
        current_value = None
        if isinstance(node.expression, NumberNode):
            current_value = node.expression.value
            # 根据值的实际类型推断 INTEGER 或 FLOAT
            if isinstance(current_value, int):
                inferred_type = "INTEGER"
            elif isinstance(current_value, float):
                inferred_type = "FLOAT"
            else:
                raise SemanticError(f"不支持的数值类型: {type(current_value)}",
                                    lineno=node.lineno, lexpos=node.lexpos)
        elif isinstance(node.expression, StringNode):
            current_value = node.expression.value
            inferred_type = "STRING"
        else:  # 如果是更复杂的表达式，类型可能是 "EXPRESSION_RESULT" 或从操作推断
            # 这里简化，如果不是直接的常量，我们就不存具体值，只标记类型
            inferred_type = rhs_type if rhs_type else "ANY_TYPE"  # rhs_type可能是表达式的推断类型

        self.symbol_table.define(var_name,
                                 sym_type=inferred_type,
                                 value=current_value,
                                 lineno=node.lineno,
                                 lexpos=node.lexpos)
        # print(f"变量 '{var_name}' 被赋值，类型: {inferred_type}")
        return "ASSIGNMENT_STATEMENT"  # 语句通常不返回值类型

    def visit_PrintNode(self, node: PrintNode):
        # 分析 print 的参数表达式
        self.visit(node.expression)
        # print 函数可以接受任何类型的参数，所以通常不需要对参数做严格类型检查
        # 除非我们想限制只能打印特定类型
        return "PRINT_STATEMENT"

    def visit_IfNode(self, node: IfNode):
        # 1. 分析条件表达式
        condition_type = self.visit(node.condition)
        # 2. 检查条件类型是否适合做条件判断 (例如，是否可以隐式转为布尔)
        #    在Python中，很多类型都可以，0, None, 空字符串/列表为False
        #    这里我们简化，不强制必须是严格的布尔类型。
        #    print(f"If 条件类型: {condition_type}")

        # 3. 分析 then 块
        self.visit(node.then_block)

        # 4. 如果有 else 块，分析它
        if node.else_block:
            self.visit(node.else_block)
        return "IF_STATEMENT"

    def visit_WhileNode(self, node: WhileNode):
        # 1. 分析条件表达式
        condition_type = self.visit(node.condition)
        # print(f"While 条件类型: {condition_type}")

        # 2. 分析循环体
        #    如果需要处理 break/continue，这里会更复杂，需要传递循环上下文
        self.visit(node.body_block)
        return "WHILE_STATEMENT"

    def visit_ForNode(self, node: ForNode):
        # 1. 分析可迭代对象 (iterable)
        iterable_name = None
        if isinstance(node.iterable, IdentifierNode):
            iterable_name = node.iterable.name
            iterable_symbol = self.symbol_table.lookup(iterable_name)
            if not iterable_symbol:
                raise SemanticError(f"变量 '{iterable_name}' 在用作 for 循环的可迭代对象前未定义。",
                                    lineno=node.iterable.lineno, lexpos=node.iterable.lexpos)
            # 在更复杂的系统中，我们会检查 iterable_symbol.sym_type 是否可迭代
            # print(f"For 循环迭代对象 '{iterable_name}' 类型: {iterable_symbol.sym_type}")
        else:
            # 如果支持 range() 或列表字面量等，这里需要进一步分析
            # 现在我们只简单访问它，不强制它是标识符
            self.visit(node.iterable)

        # 2. 定义循环变量
        #    Python的 for 循环变量在循环结束后仍然存在于作用域中。
        #    我们可以在这里将其定义到符号表，类型可以设为 "ANY_TYPE" 或 "ITERATION_VARIABLE"
        #    因为我们不知道迭代元素的具体类型。
        loop_var_name = node.identifier.name
        self.symbol_table.define(loop_var_name,
                                 sym_type="ITERATION_VARIABLE",  # 或 ANY_TYPE
                                 lineno=node.identifier.lineno,
                                 lexpos=node.identifier.lexpos)
        # print(f"For 循环变量 '{loop_var_name}' 已定义。")

        # 3. 分析循环体
        #    在循环体内，loop_var_name 是可用的
        self.visit(node.body_block)
        return "FOR_STATEMENT"

    # --- 表达式节点的访问方法 ---
    # 这些方法通常会返回表达式的“类型”（一个字符串标记，或更复杂的类型对象）

    def visit_IdentifierNode(self, node: IdentifierNode):
        var_name = node.name
        symbol = self.symbol_table.lookup(var_name)
        if not symbol:
            raise SemanticError(f"变量 '{var_name}' 在使用前未定义/赋值。",
                                lineno=node.lineno, lexpos=node.lexpos)
        # print(f"访问标识符 '{var_name}', 类型: {symbol.sym_type}")
        return symbol.sym_type  # 返回符号表中记录的类型

    def visit_NumberNode(self, node: NumberNode):
        if isinstance(node.value, int):
            return "INTEGER"
        elif isinstance(node.value, float):
            return "FLOAT"
        else:
            # 这个分支理论上不应该被执行，因为词法分析器应该已经确保了类型
            raise SemanticError(f"NumberNode 包含非预期的Python类型值: {type(node.value)}",
                                lineno=node.lineno, lexpos=node.lexpos)

    def visit_StringNode(self, node: StringNode):
        return "STRING"

    def visit_BinaryOpNode(self, node: BinaryOpNode):
        left_type = self.visit(node.left) # 可能返回 "INTEGER" 或 "FLOAT"
        right_type = self.visit(node.right)
        op = node.op.type

        if op in ['PLUS', 'MINUS', 'TIMES', 'DIVIDE']:
            if not (self._is_numeric_type(left_type) and self._is_numeric_type(right_type)):
                # ... (处理字符串拼接等) ...
                # 如果 op 是 '/'，即使两边是整数，结果也应该是浮点数 (Python 3 行为)
                if op == 'DIVIDE' and left_type == "INTEGER" and right_type == "INTEGER":
                     # 即使是整数除法，我们也可能希望结果是FLOAT以保持一致性
                     # 或者你可以引入一个专门的整数除法操作符 // 如果支持的话
                     return "FLOAT"
                raise SemanticError(f"不支持的操作: 不能对类型 '{left_type}' 和 '{right_type}' 执行 '{op}' 操作。",
                                    lineno=node.lineno, lexpos=node.lexpos)

            # 如果都是数字类型，确定结果类型
            if left_type == "FLOAT" or right_type == "FLOAT" or op == 'DIVIDE':
                return "FLOAT"
            # ITERATION_VARIABLE 或 ANY_TYPE 的处理
            elif left_type == "ITERATION_VARIABLE" or right_type == "ITERATION_VARIABLE" or \
                 left_type == "ANY_TYPE" or right_type == "ANY_TYPE":
                # 结果类型不确定，可能是FLOAT或INTEGER，取决于运行时
                # 为了安全，可以假设为FLOAT，或者引入 "NUMBER_COMPATIBLE" 类型
                return "FLOAT" # 或 "ANY_NUMERIC"
            else: # 两者都是 INTEGER (且操作不是 '/')
                return "INTEGER"

        elif op in ['GT', 'LT', 'GTE', 'LTE', 'EQ', 'NEQ']:
            # 允许数字类型 (INTEGER, FLOAT) 间的比较
            # 也允许与 ANY_TYPE, ITERATION_VARIABLE 比较
            # 检查是否有一方是数字而另一方是完全不相关的类型（如严格的STRING，如果前面没处理）
            # if not ( (self._is_numeric_type(left_type) or left_type == "ANY_TYPE" or left_type == "ITERATION_VARIABLE") and \
            #            (self._is_numeric_type(right_type) or right_type == "ANY_TYPE" or right_type == "ITERATION_VARIABLE") ):
            #     # 如果严格一点，可以对不同大类的比较发出警告或错误
            #     # 但Python本身比较灵活
            #     pass
            return "BOOLEAN"

    def visit_FunctionDefNode(self, node: FunctionDefNode):
        function_name = node.name.name
        if self.symbol_table.lookup(function_name, current_scope_only=True):
            raise SemanticError(f"函数 '{function_name}' 在当前作用域已定义", lineno=node.lineno)

        # 在父作用域中定义函数名
        # 未来可以存储参数信息: a
        self.symbol_table.define(function_name, sym_type="FUNCTION", lineno=node.lineno)

        # 进入新作用域处理函数体
        self.current_function = function_name
        self.symbol_table.enter_scope()

        # 将参数定义为新作用域的变量
        for param in node.parameters:
            self.symbol_table.define(param.name, sym_type="PARAMETER", lineno=param.lineno)

        # 分析函数体
        self.visit(node.body_block)

        # 退出函数作用域
        self.symbol_table.exit_scope()
        self.current_function = None

    def visit_ReturnNode(self, node: ReturnNode):
        if self.current_function is None:
            raise SemanticError("'return' 语句不能出现在函数外部", lineno=node.lineno)
        self.visit(node.expression)  # 分析返回的表达式

    def visit_FunctionCallNode(self, node: FunctionCallNode):
        function_name = node.name.name
        symbol = self.symbol_table.lookup(function_name)
        if not symbol or symbol.sym_type != "FUNCTION":
            raise SemanticError(f"函数 '{function_name}' 未定义或不是一个函数", lineno=node.lineno)

        # (可选) 检查参数数量
        # num_params = symbol.num_params # 假设符号表存储了参数数量
        # if len(node.arguments) != num_params:
        #     raise SemanticError(...)

        for arg_expr in node.arguments:
            self.visit(arg_expr)

        # 函数调用的类型是函数的返回类型，这里简化为 ANY_TYPE
        return "ANY_TYPE"
    # 辅助方法
    def _is_numeric_type(self, type_str):
        return type_str in ["INTEGER", "FLOAT", "ANY_TYPE", "ITERATION_VARIABLE", "PARAMETER"]  # 允许这些类型参与数值运算
        # ANY_TYPE 和 ITERATION_VARIABLE 是为了灵活性

    def _is_potentially_stringifiable(self, type_str):
        # 哪些类型可以和字符串进行 + 操作 (在我们的简化语言中)
        return type_str in ["STRING", "ANY_TYPE", "ITERATION_VARIABLE", "INTEGER"]  # 假设数字可以被转为字符串拼接


# --- 简单测试 (通常在主编译器流程中进行) ---
if __name__ == '__main__':
    # 构建一个简单的AST来测试 (手动或通过解析器)
    # 例如: x = 10 + y
    #       print(x)

    # 手动构建AST示例:
    # Program:
    #   Assignment: x = (BinaryOp: 10 + y)
    #   Print: x

    # 假设 y 未定义会触发错误
    # 假设 10 + "hello" 会触发错误

    analyzer = SemanticAnalyzer()

    # 测试1: y 未定义
    print("\n--- 测试1: y 未定义 ---")
    ast1 = ProgramNode(statements=[
        AssignmentNode(
            IdentifierNode("x", lineno=1),
            BinaryOpNode(
                NumberNode(10, lineno=1),
                types.SimpleNamespace(type='PLUS', value='+'),  # <--- 修改这里
                IdentifierNode("y", lineno=1)  # y 未定义
            ),
            lineno=1
        )
    ])
    try:
        analyzer.analyze(ast1)
    except SemanticError as e:
        print(f"捕获到预期的语义错误: {e}")
    except Exception as e:
        print(f"捕获到意外错误: {e}")

    # 测试2: 类型不匹配的加法
    # 需要先定义 y
    analyzer = SemanticAnalyzer()  # 新的分析器和符号表
    print("\n--- 测试2: 类型不匹配的加法 (10 + 'hello') ---")
    analyzer.symbol_table.define("y_str", sym_type="STRING", value="hello", lineno=0)
    ast2 = ProgramNode(statements=[
        AssignmentNode(
            IdentifierNode("x", lineno=1),
            BinaryOpNode(
                NumberNode(10, lineno=1),
                types.SimpleNamespace(type='PLUS', value='+'), # <--- 修改这里
                IdentifierNode("y_str", lineno=1)  # y_str 是 STRING
            ),
            lineno=1
        )
    ])
    try:
        analyzer.analyze(ast2)
    except SemanticError as e:
        print(f"捕获到预期的语义错误: {e}")
    except Exception as e:
        print(f"捕获到意外错误: {e}")

    # 测试3: 正常赋值和打印
    analyzer = SemanticAnalyzer()
    print("\n--- 测试3: 正常赋值和打印 ---")
    ast3 = ProgramNode(statements=[
        AssignmentNode(IdentifierNode("a", lineno=1), NumberNode(5, lineno=1), lineno=1),
        AssignmentNode(
            IdentifierNode("b", lineno=2),
            BinaryOpNode(
                IdentifierNode("a", lineno=2),
                types.SimpleNamespace(type='PLUS', value='+'), # <--- 修改这里
                NumberNode(3, lineno=2)
            ),
            lineno=2
        ),
        PrintNode(IdentifierNode("b", lineno=3), lineno=3)
    ])
    try:
        analyzer.analyze(ast3)
        print("符号表内容:", analyzer.symbol_table)
    except Exception as e:
        print(f"捕获到错误: {e}")

    # 测试4: For 循环 (iterable 未定义)
    analyzer = SemanticAnalyzer()
    print("\n--- 测试4: For 循环 (iterable 未定义) ---")
    ast4 = ProgramNode(statements=[
        ForNode(
            IdentifierNode("i", lineno=1),
            IdentifierNode("my_list", lineno=1),  # my_list 未定义
            BlockNode([PrintNode(IdentifierNode("i", lineno=2), lineno=2)], lineno=2),
            lineno=1
        )
    ])
    try:
        analyzer.analyze(ast4)
    except SemanticError as e:
        print(f"捕获到预期的语义错误: {e}")
    except Exception as e:
        print(f"捕获到意外错误: {e}")