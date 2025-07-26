# intermediate_code_generator.py
# 中间代码生成
from ast_nodes import (
    ProgramNode, AssignmentNode, PrintNode, IfNode, WhileNode, ForNode,
    BlockNode, BinaryOpNode, NumberNode, StringNode, IdentifierNode,
    FunctionDefNode, FunctionCallNode, ReturnNode
)
# 假设你的 ast_nodes.py 已经更新以包含 UnaryOpNode 如果你支持一元操作
# from ast_nodes import UnaryOpNode

from symbol_table import SymbolTable  # 假设会用到符号表信息
from quadruple import Quadruple, OP_ADD, OP_ASSIGN, OP_DIV, OP_EQ, OP_GT, OP_GTE, \
    OP_IF_FALSE_GOTO, OP_GOTO, OP_LABEL, OP_LT, OP_LTE, OP_MUL, \
    OP_NEQ, OP_PRINT_INT, OP_PRINT_STR, OP_PRINT_FLOAT, OP_SUB, OP_UMINUS,\
    OP_FUNC_BEGIN, OP_FUNC_END, OP_PARAM, OP_ARG, OP_CALL, OP_RETURN_VAL, OP_RETURN


# 导入你定义的所有操作码

class IntermediateCodeGenerator:
    """
    从AST生成四元式中间代码。
    """

    def __init__(self, symbol_table: SymbolTable):
        self.quadruples = []  # 存储生成的四元式列表
        self.temp_var_count = 0  # 用于生成临时变量名 (t0, t1, ...)
        self.label_count = 0  # 用于生成唯一标签名 (L0, L1, ...)
        self.symbol_table = symbol_table  # 主要用于查找变量信息，但生成时通常用变量名

    def _new_temp(self):
        """生成一个新的唯一临时变量名"""
        temp_name = f"t{self.temp_var_count}"
        self.temp_var_count += 1
        # (可选) 可以在符号表中将临时变量也注册进去，如果需要跟踪它们的类型等
        # self.symbol_table.define(temp_name, sym_type="TEMP_VAR", scope_level=?)
        return temp_name

    def _new_label(self):
        """生成一个新的唯一标签名"""
        label_name = f"L{self.label_count}"
        self.label_count += 1
        return label_name

    def emit(self, op, arg1, arg2, result):
        """添加一条新的四元式到列表中"""
        quad = Quadruple(op, arg1, arg2, result)
        self.quadruples.append(quad)
        # print(f"Generated Quad: {quad}") # 调试时可以取消注释

    def generate(self, ast_root: ProgramNode):
        """开始生成中间代码的入口"""
        if not isinstance(ast_root, ProgramNode):
            raise TypeError("中间代码生成的根节点必须是 ProgramNode")

        self.quadruples = []  # 重置
        self.temp_var_count = 0
        self.label_count = 0

        print("--- 开始中间代码生成 ---")
        self.visit(ast_root)
        print(f"中间代码生成完成，共 {len(self.quadruples)} 条四元式。")
        return self.quadruples

    def visit(self, node):
        """AST节点的通用访问方法 (访问者模式分发)"""
        method_name = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method_name, self.generic_visit)
        # 返回值通常是操作结果存放的“位置”（变量名、临时变量名、常量值）
        return visitor(node)

    def generic_visit(self, node):
        raise NotImplementedError(f"ICG: 没有为节点类型 {node.__class__.__name__} 定义 visit 方法")

    # --- AST节点访问方法 ---

    def visit_ProgramNode(self, node: ProgramNode):
        for statement in node.statements:
            if statement:
                self.visit(statement)

    def visit_BlockNode(self, node: BlockNode):
        for statement in node.statements:
            if statement:
                self.visit(statement)

        # --- NEW VISIT METHODS ---

    def visit_FunctionDefNode(self, node: FunctionDefNode):
        func_name = node.name.name

        # 1. 生成函数开始标记
        # 第二个参数可以存参数数量
        self.emit(OP_FUNC_BEGIN, func_name, len(node.parameters), None)

        # 2. 为每个参数生成 PARAM 指令
        for param in node.parameters:
            self.emit(OP_PARAM, param.name, None, None)

        # 3. 访问函数体
        self.visit(node.body_block)

        # 4. 生成函数结束标记
        self.emit(OP_FUNC_END, func_name, None, None)

    def visit_ReturnNode(self, node: ReturnNode):
        if node.expression:
            return_value_target = self.visit(node.expression)
            self.emit(OP_RETURN_VAL, return_value_target, None, None)
        else:
            self.emit(OP_RETURN, None, None, None)

    def visit_FunctionCallNode(self, node: FunctionCallNode):
        # 1. 为每个参数生成 ARG 指令 (压栈)
        for arg_expr in node.arguments:
            arg_target = self.visit(arg_expr)
            self.emit(OP_ARG, arg_target, None, None)

        # 2. 生成 CALL 指令
        func_name = node.name.name
        result_temp = self._new_temp()  # 用于接收返回值
        self.emit(OP_CALL, func_name, len(node.arguments), result_temp)

        return result_temp  # 函数调用的结果是这个临时变量

    def visit_AssignmentNode(self, node: AssignmentNode):
        # 1. 计算右侧表达式的值，结果会放在某个地方 (rhs_target)
        rhs_target = self.visit(node.expression)

        # 2. 生成赋值四元式
        #    左侧是 IdentifierNode，我们用它的名字
        var_name = node.identifier.name
        self.emit(OP_ASSIGN, rhs_target, None, var_name)

    def visit_PrintNode(self, node: PrintNode):
        expr_target = self.visit(node.expression)

        # 简化：假设我们能知道类型
        val_type = "UNKNOWN"
        if isinstance(expr_target, (int, float)):  # 如果visit返回的是常量值
            val_type = "FLOAT" if isinstance(expr_target, float) else "INTEGER"
        elif isinstance(expr_target, str) and not expr_target.startswith('t'):  # 不是临时变量名
            # 区分字符串常量和变量名/临时变量名
            # 如果 visit_StringNode 返回的是字符串本身
            val_type = "STRING"
        else:
            sym = self.symbol_table.lookup(str(expr_target))  # 尝试查找
            if sym:
                if sym.sym_type == "INTEGER":
                    val_type = "INTEGER"
                elif sym.sym_type == "FLOAT":
                    val_type = "FLOAT"
                elif sym.sym_type == "STRING":
                    val_type = "STRING"
                elif sym.sym_type == "BOOLEAN":
                    val_type = "BOOLEAN"
            elif isinstance(expr_target, str) and expr_target.startswith('t'):  # 临时变量
                # 我们没有简单的方法知道临时变量的类型，除非visit方法返回类型
                pass  # 保持 UNKNOWN 或默认行为

        if val_type == "INTEGER":
            self.emit(OP_PRINT_INT, expr_target, None, None)
        elif val_type == "FLOAT":
            self.emit(OP_PRINT_FLOAT, expr_target, None, None)
        elif val_type == "STRING":
            # 如果expr_target是字符串字面量，visit_StringNode应该返回它
            # 如果是变量，expr_target是变量名
            self.emit(OP_PRINT_STR, expr_target, None, None)
        else:  # 未知或布尔等
            # print(f"警告: PrintNode 打印未知或未处理类型的值: {expr_target}")
            self.emit('PRINT_ANY', expr_target, None, None)  # 通用打印，后端处理

    def visit_IfNode(self, node: IfNode):
        condition_target = self.visit(node.condition)  # 条件结果放在 condition_target

        else_label = self._new_label()
        end_if_label = self._new_label()

        # 如果条件为假，跳转到 else_label (或 end_if_label 如果没有else)
        self.emit(OP_IF_FALSE_GOTO, condition_target, None, else_label if node.else_block else end_if_label)

        # Then 块
        self.visit(node.then_block)
        if node.else_block:  # 如果有else块，then块结束后需要跳转到end_if
            self.emit(OP_GOTO, None, None, end_if_label)

        # Else 块 (如果存在)
        self.emit(OP_LABEL, else_label, None, None)  # else_label 放在这里
        if node.else_block:
            self.visit(node.else_block)

        # End If 标签 (所有路径汇合点)
        self.emit(OP_LABEL, end_if_label, None, None)

    def visit_WhileNode(self, node: WhileNode):
        loop_start_label = self._new_label()
        loop_body_label = self._new_label()  # 可选，有时直接在start_label后就是body
        loop_end_label = self._new_label()

        self.emit(OP_LABEL, loop_start_label, None, None)  # 循环开始（条件判断前）
        condition_target = self.visit(node.condition)

        # 如果条件为假，跳转到循环结束
        self.emit(OP_IF_FALSE_GOTO, condition_target, None, loop_end_label)

        # (可选) 跳转到循环体标签，或者直接是循环体代码
        # self.emit(OP_LABEL, loop_body_label, None, None)
        self.visit(node.body_block)  # 循环体

        self.emit(OP_GOTO, None, None, loop_start_label)  # 跳回循环开始处进行条件判断
        self.emit(OP_LABEL, loop_end_label, None, None)  # 循环结束

    def visit_ForNode(self, node: ForNode):
        print(f"警告: ForNode 的中间代码生成较为复杂，此处为概念性框架。")
        iterable_target = self.visit(node.iterable)  # iterable_target 是可迭代对象 (可能是变量名)
        loop_var_name = node.identifier.name

        # 概念性：需要迭代器相关的操作码
        iterator_temp = self._new_temp()
        self.emit('ITER_NEW', iterable_target, None, iterator_temp)  # iterator_temp = new_iterator(iterable)

        loop_start_label = self._new_label()
        loop_end_label = self._new_label()

        self.emit(OP_LABEL, loop_start_label, None, None)
        # has_next_temp = self._new_temp() # 临时变量存是否有下一个
        # self.emit('ITER_HAS_NEXT', iterator_temp, None, has_next_temp)
        # self.emit(OP_IF_FALSE_GOTO, has_next_temp, None, loop_end_label)

        # 简化：假设 ITER_NEXT 如果没有下一个了会跳转到 loop_end_label (或返回特殊值)
        # 或者 ITER_NEXT 将值赋给 loop_var_name，如果失败则跳转
        self.emit('ITER_NEXT_OR_JUMP', iterator_temp, loop_end_label, loop_var_name)
        # ^^^ 上面这个 'ITER_NEXT_OR_JUMP' 是一个假设的、功能强大的指令
        # 它会: loop_var_name = iterator_temp.next(); if no_next: goto loop_end_label

        self.visit(node.body_block)  # 循环体
        self.emit(OP_GOTO, None, None, loop_start_label)
        self.emit(OP_LABEL, loop_end_label, None, None)
        self.emit('ITER_DEL', iterator_temp, None, None)  # 清理迭代器 (可选)

    # --- 表达式节点的访问方法 ---
    # 这些方法返回操作结果存储的“位置”（临时变量名、变量名或常量值本身）

    def visit_IdentifierNode(self, node: IdentifierNode):
        # 标识符在表达式中直接使用其名称
        # 我们假设语义分析已确保它已定义
        return node.name

    def visit_NumberNode(self, node: NumberNode):
        # 数字常量直接作为操作数使用
        return node.value  # 返回 Python 的 int 或 float 对象

    def visit_StringNode(self, node: StringNode):
        # 字符串常量直接作为操作数使用
        return node.value  # 返回 Python 的 str 对象

    def visit_BinaryOpNode(self, node: BinaryOpNode):
        left_target = self.visit(node.left)
        right_target = self.visit(node.right)

        result_temp = self._new_temp()  # 结果存入新的临时变量

        # 将AST操作符Token类型映射到四元式操作码
        op_map = {
            'PLUS': OP_ADD, 'MINUS': OP_SUB, 'TIMES': OP_MUL, 'DIVIDE': OP_DIV,
            'EQ': OP_EQ, 'NEQ': OP_NEQ, 'LT': OP_LT, 'LTE': OP_LTE,
            'GT': OP_GT, 'GTE': OP_GTE,
            # ... 其他如 AND, OR (如果支持)
        }

        quad_op = op_map.get(node.op.type)
        if not quad_op:
            raise ValueError(f"ICG: 未知的二元操作符Token类型: {node.op.type}")

        self.emit(quad_op, left_target, right_target, result_temp)
        return result_temp  # 返回存储结果的临时变量名



