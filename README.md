# SubPy 编译器 —— python-liker compiler

SubPy 编译器是一个针对类 Python 语法的简易编译器实现，支持词法分析、语法分析、语义分析、中间代码生成、代码优化及目标代码生成等完整编译流程，并提供了可视化的用户界面以便直观展示各阶段的处理结果。

## 功能特点

- **完整的编译流程**：实现了从源代码到目标汇编代码的全流程转换
- **可视化界面**：通过分阶段选项卡展示编译各环节的输出结果
- **语法支持**：支持变量定义、数值运算、函数定义与调用、条件判断、循环结构等基础语法
- **代码优化**：包含中间代码优化功能
- **错误处理**：对语法错误、词法错误等提供基本的错误提示

## 支持的语法特性

1. **变量定义与赋值**：如 `a=1`、`b=2.5`
2. **数值运算**：支持 `+`、`-`、`*`、`/` 等基本运算
3. **函数定义与调用**：如 `def add(x,y): return x+y` 及 `c=add(a,b)`
4. **条件语句**：`if-else` 结构（需正确缩进）
5. **循环结构**：`while` 循环及嵌套循环
6. **打印输出**：`print` 语句，支持字符串和变量输出

## 使用方法

### 环境要求

- Python 3.x
- PyQt5：用于图形界面展示

### 运行方式

1. 安装依赖：`pip install PyQt5`
2. 运行主程序：`python main.py`
3. 在界面中：
   - 直接在"源代码"选项卡输入代码
   - 或通过"选择文件"按钮加载 `.py` 或 `.txt` 格式的源文件
   - 勾选"启用优化"可开启中间代码优化
   - 点击"编译"按钮执行编译流程
   - 在各选项卡查看对应阶段的输出结果

## 编译流程说明

1. **词法分析**：将源代码分解为.token（如标识符、关键字、运算符等），并记录其位置信息
2. **语法分析**：根据语法规则构建抽象语法树（AST）
3. **语义分析**：检查代码的语义正确性，构建并维护符号表
4. **中间代码生成**：将AST转换为四元式形式的中间代码
5. **代码优化**：对中间代码进行优化处理，提升执行效率
6. **目标代码生成**：将优化后的中间代码转换为汇编代码

## 测试用例

在 `test` 目录下提供了多个测试用例，涵盖不同语法特性：

- `0_基本.txt`：基本变量定义与运算
- `3_If-Else & string.txt`：条件语句与字符串
- `4_while.txt`：循环结构
- `5_def.txt`：函数定义与调用
- `6_中间代码优化.txt`：用于测试代码优化效果
- `7_缩进err.txt`：缩进错误示例
- `8_嵌套循环.txt`：嵌套循环示例

## 代码结构

- `main.py`：主程序入口，包含GUI实现和编译流程控制
- `lexer.py`：词法分析器实现
- `parser_rules.py`：语法分析规则
- `semantic_analyzer.py`：语义分析器
- `intermediate_code_generator.py`：中间代码生成器
- `intermediate_code_optimizer.py`：中间代码优化器
- `target_code_generator.py`：目标代码生成器
- `symbol_table.py`：符号表实现
- `ast_nodes.py`：抽象语法树节点定义

## 注意事项

- 严格要求正确的缩进格式（类似Python），否则会导致语法错误
- 字符串需使用引号包裹，且需正确闭合
- 函数定义、条件语句、循环语句后的代码块需正确缩进
- 目前仅支持基础语法，复杂特性（如类、异常处理等）尚未实现
