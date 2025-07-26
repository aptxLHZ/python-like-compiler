#AST语法树节点
# ast_nodes.py


def _pretty_repr(obj, indent=0):
    """一个通用的、能处理AST节点、列表和基本类型的漂亮打印辅助函数。"""
    indent_str = ' ' * indent

    if hasattr(obj, '_pretty_repr_custom'):
        # 如果对象有自定义的漂亮打印方法，就使用它
        return obj._pretty_repr_custom(indent)

    if isinstance(obj, list):
        if not obj:
            return "[]"
        items = ',\n'.join([_pretty_repr(item, indent + 4) for item in obj])
        return f"[\n{items}\n{indent_str}]"

    if isinstance(obj, Node):  # 检查是否是我们的 AST 节点
        # 自动处理所有 AST 节点
        class_name = obj.__class__.__name__
        indent_str_inner = ' ' * (indent + 4)

        # 过滤掉内部属性和位置信息
        attrs = {k: v for k, v in obj.__dict__.items()
                 if not k.startswith('_') and k not in ['lineno', 'lexpos']}

        if not attrs:
            return f"{class_name}()"

        attr_strs = []
        for name, value in attrs.items():
            value_repr = _pretty_repr(value, indent + 4)
            attr_strs.append(f"{indent_str_inner}{name}={value_repr}")

        return f"{class_name}(\n" + ',\n'.join(attr_strs) + f"\n{indent_str})"

    # 对于其他所有类型，使用标准的 repr
    return repr(obj)

class Node:
    """AST节点基类"""
    def __init__(self, lineno=None, lexpos=None):
        self.lineno = lineno  # Token的行号，用于错误报告
        self.lexpos = lexpos  # Token的位置，用于错误报告

    def __repr__(self):
        # return f"{self.__class__.__name__}({self._attrs_repr()})"
        return _pretty_repr(self)

    # def _attrs_repr(self):
    #     # 子类可以覆盖这个方法来定制它们的表示
    #     attrs = []
    #     for name, value in self.__dict__.items():
    #         if name in ['lineno', 'lexpos'] or name.startswith('_'): # 忽略内部属性和位置信息
    #             continue
    #         if isinstance(value, list):
    #             # 对列表中的每个元素调用 repr
    #             list_repr = "[" + ", ".join(repr(item) for item in value) + "]"
    #             attrs.append(f"{name}={list_repr}")
    #         else:
    #             attrs.append(f"{name}={repr(value)}")
    #     return ", ".join(attrs)
class ProgramNode(Node):
    """程序根节点"""
    def __init__(self, statements, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.statements = statements # 语句列表
class StatementNode(Node):
    """语句基类 (可选，如果需要统一处理语句)"""
    pass
class AssignmentNode(StatementNode):
    """赋值语句节点: identifier = expression"""
    def __init__(self, identifier, expression, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.identifier = identifier # IdentifierNode
        self.expression = expression # ExpressionNode
class PrintNode(StatementNode):
    """print语句节点: print(expression)"""
    def __init__(self, expression, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.expression = expression # ExpressionNode
class IfNode(StatementNode):
    """If语句节点: if condition: then_block [else: else_block]"""
    def __init__(self, condition, then_block, else_block=None, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.condition = condition     # ExpressionNode
        self.then_block = then_block   # BlockNode
        self.else_block = else_block   # BlockNode or None
class WhileNode(StatementNode):
    """While语句节点: while condition: body_block"""
    def __init__(self, condition, body_block, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.condition = condition     # ExpressionNode
        self.body_block = body_block   # BlockNode
class ForNode(StatementNode):
    """For语句节点: for identifier in iterable: body_block"""
    def __init__(self, identifier, iterable, body_block, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.identifier = identifier   # IdentifierNode (循环变量)
        self.iterable = iterable     # ExpressionNode (例如，一个列表名或range()调用)
        self.body_block = body_block   # BlockNode
class BlockNode(Node):
    """代码块节点 (由缩进产生)"""
    def __init__(self, statements, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.statements = statements # 语句列表
class ExpressionNode(Node):
    """表达式基类"""
    pass
class BinaryOpNode(ExpressionNode):
    """二元操作节点: left op right"""
    def __init__(self, left, op, right, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.left = left     # ExpressionNode
        self.op = op         # 操作符Token (例如 '+', '>', '==')
        self.right = right   # ExpressionNode

    def _attrs_repr(self): # 定制BinaryOpNode的表示
        return f"left={repr(self.left)}, op='{self.op.value if hasattr(self.op, 'value') else self.op}', right={repr(self.right)}"
class NumberNode(ExpressionNode):
    """数字节点"""
    def __init__(self, value, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.value = value # value 将是 int 或 float
class StringNode(ExpressionNode):
    """字符串节点"""
    def __init__(self, value, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.value = value # 字符串值
class IdentifierNode(ExpressionNode):
    """标识符节点 (变量名)"""
    def __init__(self, name, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.name = name # 变量名字符串
class UnaryOpNode(ExpressionNode):
    def __init__(self, op, operand, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.op = op
        self.operand = operand
class FunctionDefNode(StatementNode):
    """函数定义节点: def function_name(parameters): body_block"""
    def __init__(self, name, parameters, body_block, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.name = name          # IdentifierNode
        self.parameters = parameters  # List of IdentifierNode
        self.body_block = body_block    # BlockNode
class FunctionCallNode(ExpressionNode):
    """函数调用节点: function_name(arguments)"""
    def __init__(self, name, arguments, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.name = name          # IdentifierNode
        self.arguments = arguments    # List of ExpressionNode
class ReturnNode(StatementNode):
    """Return语句节点: return expression"""
    def __init__(self, expression, lineno=None, lexpos=None):
        super().__init__(lineno, lexpos)
        self.expression = expression  # ExpressionNode (可以为 None)
