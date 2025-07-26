# target_code_generator.py

from symbol_table import SymbolTable
class RegisterAllocator:
    def __init__(self, num_registers=4):
        self.num_registers = num_registers
        self.registers = [f"R{i}" for i in range(num_registers)]
        self.register_map = {}
        self.register_content = {}
        self.free_registers = self.registers[:]
        self.spill_count = 0

    def get_reg(self, var_name, live_out_vars_at_instr=None):
        if var_name in self.register_map:
            return self.register_map[var_name]
        if self.free_registers:
            reg = self.free_registers.pop(0)
            self._assign_reg(reg, var_name)
            return reg
        reg_to_spill = None
        if live_out_vars_at_instr:
            for reg_candidate in self.registers:
                content_var = self.register_content.get(reg_candidate)
                if content_var and content_var not in live_out_vars_at_instr:
                    reg_to_spill = reg_candidate
                    break
        if not reg_to_spill:
            reg_to_spill = self.registers[0]
        spilled_var = self.register_content.get(reg_to_spill)
        if spilled_var:
            self._release_reg_content(reg_to_spill)
        self._assign_reg(reg_to_spill, var_name)
        return reg_to_spill

    def _assign_reg(self, reg, var_name):
        self.register_map[var_name] = reg
        self.register_content[reg] = var_name
        if reg in self.free_registers:
            self.free_registers.remove(reg)

    def free_reg_containing(self, var_name):
        if var_name in self.register_map:
            reg = self.register_map.pop(var_name)
            if reg in self.register_content:
                del self.register_content[reg]
            if reg not in self.free_registers:
                self.free_registers.append(reg)
                self.free_registers.sort()

    def _release_reg_content(self, reg):
        if reg in self.register_content:
            var_in_reg = self.register_content.pop(reg)
            if var_in_reg in self.register_map and self.register_map[var_in_reg] == reg:
                del self.register_map[var_in_reg]

    def ensure_in_register(self, var_name, target_reg_name=None, code_emitter=None, live_info=None):
        if var_name in self.register_map:
            current_reg = self.register_map[var_name]
            if target_reg_name and current_reg != target_reg_name:
                if target_reg_name in self.register_content:
                    content_to_move = self.register_content[target_reg_name]
                    self._release_reg_content(target_reg_name)
                code_emitter.emit_asm(f"MOV {target_reg_name}, {current_reg}")
                self._release_reg_content(current_reg)
                self._assign_reg(target_reg_name, var_name)
                return target_reg_name
            return current_reg
        reg_for_var = None
        if target_reg_name:
            if target_reg_name in self.register_content:
                content_to_move = self.register_content[target_reg_name]
                code_emitter.emit_store_if_dirty_and_live(target_reg_name, content_to_move, live_info)
                self._release_reg_content(target_reg_name)
            reg_for_var = target_reg_name
            self._assign_reg(reg_for_var, var_name)
            if reg_for_var in self.free_registers:
                self.free_registers.remove(reg_for_var)
        else:
            reg_for_var = self.get_reg(var_name,
                                       live_out_vars_at_instr=live_info.get('live_out') if live_info else None)
        if isinstance(var_name, (int, float)):
            code_emitter.emit_asm(f"LOADI {reg_for_var}, {var_name}")
        elif var_name.startswith('t') and var_name[1:].isdigit():
            code_emitter.emit_asm(f"LOAD {reg_for_var}, M[{var_name}]")
        else:
            code_emitter.emit_asm(f"LOAD {reg_for_var}, M[{var_name}]")
        return reg_for_var
class CodeGenerator:
    def __init__(self, symbol_table: SymbolTable, num_registers=4):
        self.symbol_table = symbol_table
        self.assembly_code = []
        # Store num_registers to properly reset the allocator
        self._num_registers = num_registers
        self.reg_allocator = RegisterAllocator(num_registers=self._num_registers)
        self.liveness_info = {}  # Assuming liveness analysis is done elsewhere
        self.string_constants = {}

    def emit_asm(self, instruction_string):
        self.assembly_code.append(instruction_string)

    def generate_data_segment(self):
        self.emit_asm(".data")
        if self.symbol_table and self.symbol_table.scopes:
            global_scope = self.symbol_table.scopes[0]
            for name, symbol in global_scope.items():
                # We only want to declare global variables, not functions.
                if symbol.sym_type and "FUNCTION" not in symbol.sym_type.upper():
                    initial_value = 0
                    if symbol.value is not None and isinstance(symbol.value, (int, float)):
                        initial_value = symbol.value
                    self.emit_asm(f"{name}: .word {initial_value}")
        self.emit_asm("")

    def generate(self, intermediate_code):
        # Reset state for each new compilation
        self.assembly_code = []
        self.string_constants = {}
        self.reg_allocator = RegisterAllocator(num_registers=self._num_registers)

        # 1. Generate the data segment for global variables
        self.generate_data_segment()

        # 2. Start the text segment and jump over function definitions
        self.emit_asm(".text")
        self.emit_asm("JMP main_entry\n")

        # 3. Pass 1: Generate code for all functions
        in_function_body = False
        for i, quad in enumerate(intermediate_code):
            if quad.op == 'FUNC_BEGIN':
                in_function_body = True

            if in_function_body:
                self.process_quad(quad, i, intermediate_code)

            if quad.op == 'FUNC_END':
                in_function_body = False
                self.emit_asm("")  # Add a blank line for readability

        # 4. Define the main program entry point
        self.emit_asm("# --- Main Program Entry ---")
        self.emit_asm("main_entry:")

        # 5. Pass 2: Generate code for the main program (global scope)
        in_function_body = False
        for i, quad in enumerate(intermediate_code):
            if quad.op == 'FUNC_BEGIN':
                in_function_body = True
            elif quad.op == 'FUNC_END':
                in_function_body = False

            if not in_function_body:
                self.process_quad(quad, i, intermediate_code)

        # 6. End the main program
        self.emit_asm("HALT")

        # 7. Add any string constants to the end of the file
        if self.string_constants:
            # In a real assembler, this would go in a .data section,
            # but for simplicity, we can append it.
            self.emit_asm("\n# --- String Constants ---")
            for const_name, const_value in self.string_constants.items():
                # Escape quotes in the string value
                escaped_value = const_value.replace('"', '\\"')
                self.emit_asm(f'{const_name}: .asciiz "{escaped_value}"')

        return self.assembly_code

    def process_quad(self, quad, instruction_index, all_quads):
        """Processes a single quadruple and emits corresponding assembly instructions."""
        op, arg1, arg2, result = quad.op, quad.arg1, quad.arg2, quad.result
        i = instruction_index  # For compatibility with old logic if needed
        live_info_for_instr = self.liveness_info.get(i, {})

        # --- Reusing your logic for each quad type ---
        if op == "ASSIGN":
            reg_arg1 = self.reg_allocator.ensure_in_register(arg1, code_emitter=self, live_info=live_info_for_instr)
            reg_result = self.reg_allocator.get_reg(result, live_info_for_instr.get('live_out'))

            if reg_arg1 != reg_result:
                self.emit_asm(f"MOV {reg_result}, {reg_arg1}")

            # Store the result back to memory if it's a user variable, not a temporary
            if not str(result).startswith('t'):
                self.emit_asm(f"STORE M[{result}], {reg_result}")

        elif op in ["ADD", "SUB", "MUL", "DIV"]:
            reg_arg1 = self.reg_allocator.ensure_in_register(arg1, code_emitter=self, live_info=live_info_for_instr)
            reg_arg2 = self.reg_allocator.ensure_in_register(arg2, code_emitter=self, live_info=live_info_for_instr)

            # Decide where to store the result. We can reuse a register if the variable in it is dead.
            # Simplified logic: always get a new register for the result unless we can prove reuse is safe.
            # Here, we get a register for the result, which might be one of the operand registers.
            reg_result = self.reg_allocator.get_reg(result, live_info_for_instr.get('live_out'))

            # To perform a three-address instruction like `ADD R_res, R1, R2`, we might need a MOV.
            # `ADD R1, R2` (two-address) is more common. Let's assume two-address format: OP dest, src
            if reg_result != reg_arg1:
                self.emit_asm(f"MOV {reg_result}, {reg_arg1}")
            self.emit_asm(f"{op.upper()} {reg_result}, {reg_arg2}")

        elif op.startswith("PRINT"):
            # Simplified PRINT logic
            # If it's a string literal, we need to create a label for it.
            if isinstance(arg1, str) and not self.symbol_table.lookup(arg1) and not arg1.startswith('t'):
                str_label = f"_str_const_{len(self.string_constants)}"
                self.string_constants[str_label] = arg1
                self.emit_asm(f"PRINT_STR {str_label}")
            else:  # It's a variable or a number
                reg_to_print = self.reg_allocator.ensure_in_register(arg1, code_emitter=self,
                                                                     live_info=live_info_for_instr)
                # We need a way to distinguish types at runtime or rely on opcodes
                # Assuming PRINT_INT for now for simplicity as in your example.
                self.emit_asm(f"PRINT_INT {reg_to_print}")

        elif op == 'FUNC_BEGIN':
            self.emit_asm(f"# --- Function: {arg1} ---")
            self.emit_asm(f"{arg1}:")
            self.emit_asm("PUSH FP   # Prologue: Save old frame pointer")
            self.emit_asm("MOV FP, SP  # Prologue: Set new frame pointer")

        elif op == 'PARAM':
            # This is a declaration. The actual parameter access will be handled
            # when the parameter name (e.g., 'x') is used in an expression inside the function.
            # Correct implementation requires calculating offset from FP.
            pass

        elif op == 'ARG':
            reg_arg = self.reg_allocator.ensure_in_register(arg1, code_emitter=self)
            self.emit_asm(f"PUSH {reg_arg}  # Push argument '{arg1}'")

        elif op == 'CALL':
            # func_name=arg1, num_args=arg2, result_temp=result
            self.emit_asm(f"CALL {arg1}")
            # The return value is conventionally in a fixed register (e.g., R0).
            # We move it to the temporary variable's assigned register.
            reg_result = self.reg_allocator.get_reg(result)
            if reg_result != 'R0':
                self.emit_asm(f"MOV {reg_result}, R0  # Get return value into {result}")
            # Caller cleans up the stack
            if arg2 and int(arg2) > 0:
                self.emit_asm(f"ADD SP, SP, {int(arg2) * 4} # Clean up {arg2} args from stack")

        elif op == 'RETURN_VAL':
            reg_val = self.reg_allocator.ensure_in_register(arg1, code_emitter=self)
            # Put the return value in the conventional register R0
            if reg_val != 'R0':
                self.emit_asm(f"MOV R0, {reg_val} # Set return value")
            # Epilogue
            self.emit_asm("MOV SP, FP  # Epilogue: Deallocate local vars")
            self.emit_asm("POP FP      # Epilogue: Restore old frame pointer")
            self.emit_asm("RET         # Return to caller")

        elif op == 'FUNC_END':
            # This handles functions that might not have an explicit return statement.
            self.emit_asm("# Implicit return at end of function")
            self.emit_asm("MOV R0, 0   # Default return value is 0")
            self.emit_asm("MOV SP, FP  # Epilogue")
            self.emit_asm("POP FP      # Epilogue")
            self.emit_asm("RET")




if __name__ == '__main__':
    st = SymbolTable()
    st.define("a", sym_type="INTEGER", lineno=1)
    st.define("b", sym_type="INTEGER", lineno=1)
    st.define("c", sym_type="INTEGER", lineno=1)

    final_quads_for_gen = [
        ('ASSIGN', 1, '_', 'a'),
        ('ASSIGN', 1, '_', 'b'),
        ('ASSIGN', 1, '_', 'c'),
        ('DIV', 'b', 'c', 't1'),
        ('ADD', 6, 't1', 'a'),
        ('ASSIGN', 'a', '_', 'b'),
        ('DIV', 'b', 'c', 't5'),
        ('ADD', 6, 't5', 'c'),
        ('PRINT_INT', 'a', '_', '_'),
        ('PRINT_INT', 'b', '_', '_'),
        ('PRINT_INT', 'c', '_', '_'),
        ('PRINT_STR', "End of calculation", '_', '_'),
        ('PRINT_INT', 12345, '_', '_'),
    ]

    code_gen = CodeGenerator(st, num_registers=3)
    assembly_output = code_gen.generate(final_quads_for_gen)

    for line in assembly_output:
        print(line)