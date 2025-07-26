from quadruple import Quadruple


class Optimizer:
    def __init__(self):
        self.value_map = {}  # 变量->值的映射
        self.expr_map = {}  # 表达式->结果变量的映射
        self.used_vars = set()  # 跟踪所有被使用的变量

    def optimize(self, quadruples: list):
        print("--- 开始中间代码优化 (改进版) ---")
        optimized_quads = []

        # 第一遍：收集所有被使用的变量
        for quad in quadruples:
            if quad.arg1 and isinstance(quad.arg1, str) and not quad.arg1.startswith('t'):
                self.used_vars.add(quad.arg1)
            if quad.arg2 and isinstance(quad.arg2, str) and not quad.arg2.startswith('t'):
                self.used_vars.add(quad.arg2)
            if quad.result and isinstance(quad.result, str) and not quad.result.startswith('t'):
                self.used_vars.add(quad.result)

        # 第二遍：实际优化
        for quad in quadruples:
            self.process_quad(quad, optimized_quads)

        print(f"中间代码优化完成。优化前 {len(quadruples)} 条，优化后 {len(optimized_quads)} 条。")
        return optimized_quads

    def process_quad(self, quad, optimized_quads):
        op, arg1, arg2, result = quad.op, quad.arg1, quad.arg2, quad.result

        # 解析操作数的真实值
        arg1 = self.resolve_value(arg1)
        arg2 = self.resolve_value(arg2) if arg2 is not None else None

        if op in ['ADD', 'SUB', 'MUL', 'DIV']:
            # 常量折叠
            if isinstance(arg1, (int, float)) and isinstance(arg2, (int, float)):
                if op == 'ADD':
                    val = arg1 + arg2
                elif op == 'SUB':
                    val = arg1 - arg2
                elif op == 'MUL':
                    val = arg1 * arg2
                elif op == 'DIV':
                    val = arg1 / arg2 if arg2 != 0 else float('inf')
                self.value_map[result] = val
                return

            # 公共子表达式消除
            expr_key = (op, arg1, arg2)
            if expr_key in self.expr_map:
                prev_result = self.expr_map[expr_key]
                self.value_map[result] = prev_result
                return

            # 记录新表达式
            self.expr_map[expr_key] = result
            optimized_quads.append(Quadruple(op, arg1, arg2, result))

        elif op == 'ASSIGN':
            # 处理赋值语句
            if result in self.used_vars or not result.startswith('t'):
                # 如果是用户变量或需要保留的变量，生成赋值语句
                optimized_quads.append(Quadruple(op, arg1, None, result))

            # 更新值映射
            self.value_map[result] = arg1

        else:
            # 处理其他操作（如PRINT）
            optimized_quads.append(Quadruple(op, arg1, arg2, result))

    def resolve_value(self, value):
        """解析操作数的真实值，保留用户变量名"""
        if isinstance(value, str) and value in self.value_map:
            # 对于用户变量，保留其名称
            if value in self.used_vars:
                return value
            # 对于临时变量，解析其真实值
            return self.resolve_value(self.value_map[value])
        return value
