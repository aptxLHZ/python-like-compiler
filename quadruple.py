# quadruple.py
# 定义四元式结构

class Quadruple:
    """
    表示一条四元式指令。
    格式: (op, arg1, arg2, result)
    """
    def __init__(self, op, arg1, arg2, result):
        self.op = op  # 操作符 (字符串, e.g., 'ADD', 'ASSIGN', 'IF_FALSE_GOTO', 'LABEL')
        self.arg1 = arg1  # 第一个参数 (变量名, 常量, 临时变量名, 标签名, 或 None)
        self.arg2 = arg2  # 第二个参数 (同上)
        self.result = result  # 结果 (变量名, 临时变量名, 标签名, 或 None)

    def __repr__(self):
        return self.__str__()  # 让repr使用str的格式

    def __str__(self):
        # 定义标准列宽
        op_width = 15
        arg1_width = 15
        arg2_width = 15
        result_width = 15

        # 将None转换为占位符
        s_op = str(self.op)
        s_arg1 = str(self.arg1) if self.arg1 is not None else "_"
        s_arg2 = str(self.arg2) if self.arg2 is not None else "_"
        s_result = str(self.result) if self.result is not None else "_"

        # 特殊格式化标签指令
        if self.op == 'LABEL':
            return f"{s_arg1}:"

        # 标准四元式格式 (OP, ARG1, ARG2, RESULT)
        return f"{s_op:<{op_width}} {s_arg1:<{arg1_width}} {s_arg2:<{arg2_width}} {s_result:<{result_width}}"

# 定义一些常用的操作码 (opcodes)
OP_ASSIGN = 'ASSIGN'
OP_ADD = 'ADD'
OP_SUB = 'SUB'
OP_MUL = 'MUL'
OP_DIV = 'DIV'
OP_UMINUS = 'UMINUS' # 一元负号

OP_EQ = 'EQ' # ==
OP_NEQ = 'NEQ' # !=
OP_LT = 'LT' # <
OP_LTE = 'LTE' # <=
OP_GT = 'GT' # >
OP_GTE = 'GTE' # >=

OP_GOTO = 'GOTO'
OP_IF_FALSE_GOTO = 'IF_FALSE_GOTO' # 如果条件为假则跳转
OP_LABEL = 'LABEL'

OP_PRINT_INT = 'PRINT_INT'
OP_PRINT_FLOAT = 'PRINT_FLOAT'
OP_PRINT_STR = 'PRINT_STR'
OP_PRINT_BOOL = 'PRINT_BOOL' # 如果你的print支持布尔

# --- NEW FUNCTION OPCODES ---
OP_FUNC_BEGIN = 'FUNC_BEGIN' # 标记函数开始
OP_FUNC_END = 'FUNC_END'   # 标记函数结束
OP_PARAM = 'PARAM'       # 声明一个参数
OP_ARG = 'ARG'           # 传递一个参数
OP_CALL = 'CALL'         # 函数调用
OP_RETURN_VAL = 'RETURN_VAL' # 带返回值的返回
OP_RETURN = 'RETURN'       # 无返回值的返回

OP_HALT = 'HALT' # 程序结束