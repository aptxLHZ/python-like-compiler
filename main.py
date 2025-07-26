import sys
import os
import argparse
from io import StringIO
import traceback
from contextlib import redirect_stdout, redirect_stderr

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTextEdit, QFileDialog, QLabel, QCheckBox, QTabWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# --- 导入所有的编译器模块 ---
from lexer import get_lexer_instance
from parser_rules import get_parser_instance
from ast_nodes import ProgramNode
from semantic_analyzer import SemanticAnalyzer, SemanticError
from intermediate_code_generator import IntermediateCodeGenerator
from intermediate_code_optimizer import Optimizer
from target_code_generator import CodeGenerator

def add_line_numbers(text):
    """接收一段文本，返回带行号的新文本。"""
    lines = text.splitlines()
    numbered_lines = [f"{i+1:03d}| {line}" for i, line in enumerate(lines)]
    return "\n".join(numbered_lines)

# --- NEW: 创建一个简单的日志捕获器给 PLY 使用 ---
class PlyLogger:
    def __init__(self, stream):
        self.stream = stream

    def info(self, msg, *args, **kwargs):
        self.stream.write(msg % args + '\n')

    def warning(self, msg, *args, **kwargs):
        self.stream.write("警告: " + (msg % args) + '\n')

    def error(self, msg, *args, **kwargs):
        self.stream.write("错误: " + (msg % args) + '\n')

    def critical(self, msg, *args, **kwargs):
        self.stream.write("严重错误: " + (msg % args) + '\n')



# ==============================================================================
# 核心编译逻辑
# (使用redirect_stdout捕获内部 print)
# ==============================================================================

def run_lexical_analysis(source_code, tabsize=4):
    log_stream = StringIO()
    lexer = get_lexer_instance(tabsize=tabsize)
    lexer.input(source_code)
    tokens = []
    while True:
        tok = lexer.token()
        if not tok: break
        tokens.append(tok)
        value_repr = repr(tok.value) if tok.type == 'STRING' else str(tok.value)
        print(f"类型: {tok.type:<10s} 值: {value_repr:<40s} 行号: {tok.lineno:<3d} 位置: {tok.lexpos:<4d}", file=log_stream)
    return tokens, log_stream.getvalue()


def run_syntax_analysis(source_code, ply_logger=None, tabsize=4, parser_debug=False):
    log_stream = StringIO()
    parser_lexer = get_lexer_instance(tabsize=tabsize)
    # --- MODIFIED: 将 logger 传递给 PLY ---
    parser = get_parser_instance(debug=parser_debug, errorlog=ply_logger)
    ast_tree = parser.parse(input=source_code, lexer=parser_lexer)
    if not ast_tree:
        if source_code.strip():
            raise SyntaxError("语法分析未能生成 AST。请检查语法。")
        ast_tree = ProgramNode(statements=[])
    print(repr(ast_tree), file=log_stream)
    return ast_tree, log_stream.getvalue()


def run_semantic_analysis(ast_tree):
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast_tree)
    return analyzer


def run_intermediate_code_generation(ast_tree, symbol_table):
    icg = IntermediateCodeGenerator(symbol_table)
    intermediate_code = icg.generate(ast_tree)
    return intermediate_code


def run_optimization(intermediate_code):
    opt = Optimizer()
    optimized_code = opt.optimize(list(intermediate_code))
    return optimized_code


def run_target_code_generation(code, symbol_table):
    code_gen = CodeGenerator(symbol_table, num_registers=3)
    assembly_output = code_gen.generate(code)
    return assembly_output


# ==============================================================================
# GUI 部分
# ==============================================================================
class CompilerGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('SubPy 编译器 - 分阶段可视化')
        self.setGeometry(100, 100, 1000, 700)
        self.initUI()
        self.filepath = None

    # def initUI(self):
    #     main_layout = QVBoxLayout()
    #
    #     # 顶部控制栏
    #     top_bar = QHBoxLayout()
    #     self.btn_open = QPushButton('选择文件')
    #     self.btn_open.clicked.connect(self.open_file)
    #     self.lbl_filepath = QLabel('未选择文件')
    #     self.lbl_filepath.setStyleSheet("font-style: italic; color: grey;")
    #     self.cb_optimize = QCheckBox('启用优化')
    #     self.cb_optimize.setChecked(True)
    #     self.btn_compile = QPushButton('编译')
    #     self.btn_compile.clicked.connect(self.run_full_compilation)
    #
    #     top_bar.addWidget(self.btn_open)
    #     top_bar.addWidget(self.lbl_filepath, 1)
    #     top_bar.addSpacing(20)
    #     top_bar.addWidget(self.cb_optimize)
    #     top_bar.addWidget(self.btn_compile)
    #     main_layout.addLayout(top_bar)
    #
    #     # 选项卡区域
    #     self.tabs = QTabWidget()
    #     self.tab_map = {}
    #
    #     # --- MODIFIED: 拆分选项卡 ---
    #     tab_names = [
    #         "源代码", "1. 词法分析", "2. 语法分析 (AST)", "3. 符号表",
    #         "4. 中间代码", "5. 汇编代码", "完整日志"
    #     ]
    #
    #     for name in tab_names:
    #         editor = QTextEdit()
    #         editor.setFont(QFont("Courier New", 10))
    #         editor.setReadOnly(True)
    #         if name == "源代码":
    #             editor.setReadOnly(False)
    #             editor.setPlaceholderText("在这里输入或粘贴源代码...")
    #         self.tabs.addTab(editor, name)
    #         self.tab_map[name] = editor
    #
    #     main_layout.addWidget(self.tabs)
    #     self.setLayout(main_layout)

    def initUI(self):
        main_layout = QVBoxLayout()

        # 顶部控制栏
        top_bar = QHBoxLayout()
        self.btn_open = QPushButton('选择文件')
        self.btn_open.clicked.connect(self.open_file)
        self.lbl_filepath = QLabel('未选择文件')
        self.lbl_filepath.setStyleSheet("font-style: italic; color: grey;")
        self.cb_optimize = QCheckBox('启用优化')
        self.cb_optimize.setChecked(True)
        self.btn_compile = QPushButton('编译')
        self.btn_compile.clicked.connect(self.run_full_compilation)

        top_bar.addWidget(self.btn_open)
        top_bar.addWidget(self.lbl_filepath, 1)
        top_bar.addSpacing(20)
        top_bar.addWidget(self.cb_optimize)
        top_bar.addWidget(self.btn_compile)
        main_layout.addLayout(top_bar)

        # 选项卡区域
        self.tabs = QTabWidget()
        self.tab_map = {}

        # --- MODIFIED: 拆分选项卡 ---
        tab_names = [
            "源代码", "1. 词法分析", "2. 语法分析 (AST)", "3. 符号表",
            "4. 中间代码", "5. 汇编代码", "完整日志"
        ]

        for name in tab_names:
            editor = QTextEdit()
            editor.setFont(QFont("Courier New", 10))
            # 源代码框仍然是可编辑的
            is_readonly = name != "源代码"
            editor.setReadOnly(is_readonly)

            if name == "源代码":
                editor.setPlaceholderText("在这里输入或粘贴源代码...")

            # --- NEW: 创建一个独立的显示框来展示带行号的源代码 ---
            # 我们将把源代码框和行号显示框放在一个水平布局里
            if name == "源代码":
                self.source_editor_widget = QWidget()
                source_layout = QHBoxLayout(self.source_editor_widget)
                source_layout.setContentsMargins(0, 0, 0, 0)
                source_layout.setSpacing(0)

                self.line_number_area = QTextEdit()
                self.line_number_area.setFont(QFont("Courier New", 10))
                self.line_number_area.setReadOnly(True)
                self.line_number_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.line_number_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.line_number_area.setFixedWidth(40)
                self.line_number_area.setStyleSheet(
                    "QTextEdit { background-color: #f0f0f0; color: #888; border: none; }")

                source_layout.addWidget(self.line_number_area)
                source_layout.addWidget(editor)

                self.tabs.addTab(self.source_editor_widget, name)

            else:
                self.tabs.addTab(editor, name)

            self.tab_map[name] = editor

        # 同步滚动条
        self.tab_map["源代码"].verticalScrollBar().valueChanged.connect(
            self.line_number_area.verticalScrollBar().setValue
        )
        self.tab_map["源代码"].textChanged.connect(self.update_line_numbers)

        self.update_line_numbers()  # 初始化行号

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def update_line_numbers(self):
        """当源代码文本变化时，更新行号区域"""
        editor = self.tab_map["源代码"]
        line_count = editor.document().blockCount()
        self.line_number_area.setText('\n'.join(str(i) for i in range(1, line_count + 1)))

    def open_file(self):
        options = QFileDialog.Options()
        filepath, _ = QFileDialog.getOpenFileName(self, "选择源文件", "",
                                                  "Python Files (*.py);;Text Files (*.txt);;All Files (*)",
                                                  options=options)
        if filepath:
            self.filepath = filepath
            self.lbl_filepath.setText(filepath)
            self.lbl_filepath.setStyleSheet("")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    # 直接设置文本，update_line_numbers 会自动被 textChanged 信号触发
                    self.tab_map["源代码"].setPlainText(f.read())
                self.clear_outputs()
            except Exception as e:
                self.tab_map["完整日志"].setPlainText(f"无法读取文件: {e}")



    def clear_outputs(self):
        for name, editor in self.tab_map.items():
            if name != "源代码":
                editor.clear()

    def run_full_compilation(self):
        self.clear_outputs()
        source_code = self.tab_map["源代码"].toPlainText()
        if not source_code.strip():
            self.tab_map["完整日志"].setPlainText("错误：源代码为空。")
            return

        full_log_stream = StringIO()
        # --- NEW: 在日志开头添加带行号的源代码 ---
        full_log_stream.write("--- 源代码 ---\n")
        full_log_stream.write(add_line_numbers(source_code))
        full_log_stream.write("\n" + "-" * 40 + "\n\n")

        ply_logger = PlyLogger(full_log_stream)

        def log_stage_header(stage_name):
            full_log_stream.write(f"--- {stage_name} ---\n")

        def log_stage_footer():
            full_log_stream.write("-" * 40 + "\n\n")

        try:
            # 使用 with 语句捕获所有深层 print
            with redirect_stdout(full_log_stream), redirect_stderr(full_log_stream):

                # Stage 1: Lexical Analysis
                log_stage_header("1. 词法分析")
                tokens, log = run_lexical_analysis(source_code)
                self.tab_map["1. 词法分析"].setPlainText(log)
                full_log_stream.write(log)
                log_stage_footer()

                # Stage 2: Syntax Analysis
                log_stage_header("2. 语法分析 (AST)")
                ast_tree, log = run_syntax_analysis(source_code, ply_logger=ply_logger)
                self.tab_map["2. 语法分析 (AST)"].setPlainText(log)
                full_log_stream.write(log)
                log_stage_footer()

                # Stage 3: Semantic Analysis
                log_stage_header("3. 语义分析与符号表")
                analyzer = run_semantic_analysis(ast_tree)
                symbol_table_log = str(analyzer.symbol_table)
                self.tab_map["3. 符号表"].setPlainText(symbol_table_log)
                full_log_stream.write(symbol_table_log)
                log_stage_footer()

                symbol_table = analyzer.symbol_table

                # Stage 4: Intermediate Code Generation
                log_stage_header("4. 中间代码生成")
                intermediate_code = run_intermediate_code_generation(ast_tree, symbol_table)
                ic_display_log = "\n".join([f"{i:03d}: {q}" for i, q in enumerate(intermediate_code)])
                self.tab_map["4. 中间代码"].setPlainText(ic_display_log)
                full_log_stream.write(ic_display_log + "\n")
                log_stage_footer()

                # Stage 5: Optimization
                optimized_code = intermediate_code
                if self.cb_optimize.isChecked():
                    log_stage_header("4a. 中间代码优化")
                    optimized_code = run_optimization(intermediate_code)
                    opt_display_log = "\n".join([f"{i:03d}: {q}" for i, q in enumerate(optimized_code)])
                    self.tab_map["4. 中间代码"].append("\n\n--- 优化后四元式 ---\n" + opt_display_log)
                    full_log_stream.write("--- 优化后四元式 ---\n")
                    full_log_stream.write(opt_display_log + "\n")
                    log_stage_footer()

                # Stage 6: Target Code Generation
                log_stage_header("5. 目标代码生成")
                assembly_output = run_target_code_generation(optimized_code, symbol_table)
                assembly_display_log = "\n".join(assembly_output)
                self.tab_map["5. 汇编代码"].setPlainText(assembly_display_log)
                full_log_stream.write(assembly_display_log + "\n")
                log_stage_footer()

                # 注意：这里的 print 也会被 with 块捕获
                print("--- 编译成功完成！ ---")

        except Exception as e:
            # --- THIS IS THE KEY FIX ---
            # 我们现在在 except 块中，但 full_log_stream 已经包含了
            # 发生错误之前的所有成功日志和调试信息。
            # 我们现在将错误信息也手动写入这个流。

            full_log_stream.write("\n" + "=" * 15 + " 编译错误 " + "=" * 15 + "\n")
            if isinstance(e, (SemanticError, SyntaxError)):
                # 直接将错误对象的字符串表示写入流
                full_log_stream.write(str(e))
            else:
                # 对于其他异常，将堆栈跟踪信息写入流
                full_log_stream.write("发生未预期的错误:\n")
                traceback.print_exc(file=full_log_stream)
            full_log_stream.write("\n" + "=" * 40)

        # 无论成功或失败，都显示并保存最终的完整日志
        final_log_content = full_log_stream.getvalue()
        self.tab_map["完整日志"].setText(final_log_content)
        self.save_log_file(final_log_content)

    def save_log_file(self, log_content):
        # ... (此方法不变) ...
        if self.filepath:
            log_filename = os.path.splitext(os.path.basename(self.filepath))[0] + "_compile_log.txt"
            log_filepath = os.path.join(os.path.dirname(self.filepath), log_filename)
            try:
                with open(log_filepath, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                self.tabs.setCurrentWidget(self.tab_map["完整日志"])
                self.tab_map["完整日志"].append(f"\n--- 日志已保存到: {log_filepath} ---")
            except Exception as e:
                self.tab_map["完整日志"].append(f"\n--- 无法保存日志: {e} ---")


# ==============================================================================
# 启动逻辑
# ==============================================================================
def main():
    app = QApplication(sys.argv)
    gui = CompilerGUI()
    gui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
