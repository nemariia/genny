import ast


class CodeStructure:
    """
    A class to represent code structure
    """

    def __init__(self):
        self.imports = []
        self.classes = []
        self.functions = []
        self.variables = []

    def add_class(self, class_info):
        self.classes.append(class_info)

    def add_function(self, function_info):
        self.functions.append(function_info)

    def add_variable(self, variable_info):
        self.variables.append(variable_info)

    def add_import(self, import_info):
        self.imports.append(import_info)

    def to_dict(self):
        # Dictionary to collect data
        data = {}

        # Handling imports
        if self.imports:
            data['imports'] = [self.format_imports(imp) for imp in self.imports if imp]

        # Handling classes
        if self.classes:
            data['classes'] = [self.format_class(cl) for cl in self.classes if cl]

        # Handling classes
        if self.functions:
            data['functions'] = [self.format_function(func) for func in self.functions if func]

        # Handling classes
        if self.variables:
            data['variables'] = [self.format_variable(var) for var in self.variables if var]

        return data

    def format_imports(self, imports):
        formatted_imports = []
        for item in imports:
            if isinstance(item, tuple) and len(item) == 2:
                module, alias = item
                if alias:
                    formatted_imports.append(f"{module} as {alias}")
                else:
                    formatted_imports.append(module)
            elif isinstance(item, str):  # Handle cases where item is a string
                formatted_imports.append(item)
            else:
                formatted_imports.append("Invalid import format")
        return formatted_imports

    def format_class(self, cl):
        # Construct class dictionary, skipping empty or null attributes
        class_dict = {
            'name': cl['name'],
            'docstring': cl['docstring'] if cl['docstring'] else None,
            'base_classes': cl['base_classes'] if cl['base_classes'] else None,
            'methods': [self.format_method(method)
                        for method in cl['methods'] if method],
            'attributes': cl['attributes'] if cl['attributes'] else None
        }
        # Remove keys with None values or empty lists
        return {k: v for k, v in class_dict.items() if v}

    def format_method(self, method):
        # Similar to format_class, construct method dict, filtering out empty values
        method_dict = {
            'name': method['name'],
            'docstring': method['docstring'] if method['docstring'] else None,
            'parameters': method['parameters'] if method['parameters'] else None,
            'return_type': method['return_type'] if method['return_type'] else None
        }
        return {k: v for k, v in method_dict.items() if v}

    def format_function(self, func):
        return func

    def format_variable(self, var):
        return var

    def reset(self):
        self.classes.clear()
        self.functions.clear()
        self.variables.clear()
        self.imports.clear()


class CodeParser:
    def __init__(self, file_system):
        self.file_system = file_system
        self.code_structure = CodeStructure()
        self.docstrings = []

    def parse_code(self, file_path):
        source_code = self.file_system.read_file(file_path)
        tree = ast.parse(source_code)
        return self.build_code_structure(tree)

    def build_code_structure(self, ast_tree):
        self.code_structure.reset()
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.ClassDef):
                self.code_structure.add_class(self.get_class_details(node))
            elif isinstance(node, ast.FunctionDef):
                # TODO: handle nested functions and decorators
                parent = next((n for n in ast.walk(ast_tree)
                               if node in ast.iter_child_nodes(n)), None)
                if isinstance(parent, ast.ClassDef):
                    pass
                else:
                    self.code_structure.add_function(
                        self.get_function_details(node))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                self.code_structure.add_import(self.get_import_details(node))

        return self.code_structure

    def get_class_details(self, node):
        # Inheritance details
        base_classes = [self._get_name(base) for base in node.bases]

        # Class methods and attributes
        methods = []
        attributes = []
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                methods.append(self.get_function_details(child))
            elif isinstance(child, (ast.Assign, ast.AnnAssign)):
                # Handling both normal and annotated assignments
                for target in (child.targets if hasattr(child, 'targets')
                               else [child.target]):
                    if isinstance(target, ast.Name):
                        attributes.append({
                            'name': target.id,
                            'value': self._get_value(child.value)})

        return {
            'name': node.name,
            'docstring': ast.get_docstring(node),
            'base_classes': base_classes,
            'methods': methods,
            'attributes': attributes
            }

    # Function to analyze return types
    def return_types(self, func_ast):
        """
        Determine the return type of a function or method.
        """
        for node in ast.walk(func_ast):
            if isinstance(node, ast.Return):
                if node.value:
                    if isinstance(node.value, ast.Name):
                        return f"Returns a variable of type inferred by its use: {node.value.id}"
                    elif isinstance(node.value, ast.Call):
                        if isinstance(node.value.func, ast.Attribute):
                            obj = node.value.func.value
                            obj_id = getattr(obj, 'id', 'complex expression')
                            return f"Returns the result of a method call: {node.value.func.attr} on object {obj_id}"
                        return f"Returns the result of function call: {node.value.func.id}"
                    elif isinstance(node.value, ast.Attribute):
                        return f"Returns an attribute: {ast.unparse(node.value)}"
                    else:
                        return f"Returns a value of type: {type(node.value).__name__}"
                else:
                    return "Returns None"
        return "Returns None"



    def get_function_details(self, node):
        parameters = [param.arg for param in node.args.args]
        return {
            'name': node.name,
            'docstring': ast.get_docstring(node),
            'parameters': parameters,
            'return_type': self.return_types(node)
            }

    def _get_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return None

    def _get_value(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        return str(ast.dump(node))

    def get_import_details(self, node):
        if isinstance(node, ast.Import):
            names = [(alias.name, alias.asname) for alias in node.names]
        else:  # ast.ImportFrom
            names = [(f"{node.module}.{alias.name}", alias.asname) for alias in node.names]
        return names

    def get_docstrings(self, file_path):
        """
        Getting all docstrings from the code file

        Parameters
        ----------
        file_path : String

        Returns
        -------
        an array of docstrings

        """
        source_code = self.file_system.read_file(file_path)
        tree = ast.parse(source_code)

        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                doc = ast.get_docstring(node)
                if doc:
                    self.docstrings.append(doc)  # Only add docstrings if they exist
        return self.docstrings
