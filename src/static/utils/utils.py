import os
from loguru import logger
import subprocess


def get_wxapkg_paths(wxapkgs_dir):
    """
        Get all wxapkg paths in the wxapkgs_dir.

        -------
        Parameters:
        - dataset_dir: str
            Absolute path of wxapkg datasets

        -------
        Return:
        - wxapkg_paths: list
            A list of wxapkg absolute path in wxapkgs_dir
    """
    wxapkg_paths = []
    for root, dirs, files in os.walk(wxapkgs_dir):
        for file in files:
            if file.endswith('.wxapkg'):
                wxapkg_paths.append(root + '/' + file)
    return wxapkg_paths


def get_miniapp_paths(decompile_dir):
    """
        Get all miniapp paths in the decompile_dir.

        -------
        Parameters:
        - decompile_dir: str
            Absolute path of all decompile wxapkg datasets

        -------
        Return:
        - miniapp_paths: list
            A list of miniapp absolute path in the decompile_dir
    """
    miniapp_paths = os.listdir(decompile_dir)
    return list(os.path.join(decompile_dir, miniapp_path) for miniapp_path in miniapp_paths)


def execute_cmd(command):
    """
        Exucute shell command.
    """
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = process.communicate()
    code = process.returncode
    out_str = None
    if stdout is not None:
        out_str = stdout.decode('utf-8')
    return code == 0, out_str


def get_page_expr_node(pdg_node):
    """
        Get page/app ExpressionStatement in the PDG.

        -------
        Parameters:
        - pdg_node: Node
            Output of build_pdg.get_data_flow(input_file, benchmarks)

        -------
        Return:
        - page_expr_node: Node
            The Expression Statement of Page Object
    """
    # TODO: Design a more robust method to find PageExpr Node
    for child in pdg_node.children:
        if child.name == "ExpressionStatement":
            if len(child.children) > 0 and child.children[0].name == "CallExpression" \
                    and child.children[0].children[0].name == 'Identifier':
                if child.children[0].children[0].attributes["name"] in ("Page", "App"):
                    return child
    return None


def get_page_method_nodes(page_expr_node):
    """
        Get page/app method nodes in the PDG.

        -------
        Parameters:
        - pdg_node: Node
            Output of build_pdg.get_data_flow(input_file, benchmarks)

        -------
        Return:
        - page_method_nodes: dict
            A dict of {mothod_name : method_node}
    """
    page_method_nodes = {}
    # found page expression
    for method_node in page_expr_node.children[0].children[1].children:  # method_node: Property
        if method_node.name == 'Property':
            if method_node.attributes["value"]["type"] == "FunctionExpression":
                # handle node
                method_name = method_node.children[0].attributes['name']
                page_method_nodes[method_name] = method_node
    return page_method_nodes
