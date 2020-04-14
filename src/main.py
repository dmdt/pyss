import argparse
import os
from sys import exit
from typing import TextIO
from lexer import lexer
from lexer.token import Token, TokenClass
from syntaxer import syntaxer
from syntaxer.syntaxer import SyntaxParseError
from syntaxer.lang_dict import LangDict, SignatureType
from codegenerator.code_generator import CodeGenerator
from parsetree.parse_tree import ParseTree
from semanticanalyzer.symbol_table import SymbolTable
from semanticanalyzer.semantic_analyzer import SemanticError

parser = argparse.ArgumentParser(description="Interpreter for converting .pce files into .gpss.")
parser.add_argument(
    'input',
    type=str,
    help="File with source code to process."
)
parser.add_argument(
    '-lo',
    action='store_true',
    help="Verbose lexer output."
)
parser.add_argument(
    '-so',
    action='store_true',
    help="Verbose syntaxer output."
)
arguments = parser.parse_args()

# Checking if file has correct extension
path = arguments.input
print(f"Input file: {path}")

if path[-4:] != ".pce":
    print("Incorrect file.")
    exit(1)

if not os.path.exists(path):
    print("File doesn't exists.")
    exit(1)

if os.stat(path).st_size == 0:
    print("File is empty.")
    exit(1)

# Language dictionary
lang_dict = LangDict()
lang_dict.add_word("q", SignatureType.operator, "QUEUE", 1, [
    TokenClass.word
])
lang_dict.add_word("dq", SignatureType.operator, "DEPART", 1, [
    TokenClass.word
])
lang_dict.add_word("gen", SignatureType.operator, "GENERATE", 1, [
    TokenClass.string
])
lang_dict.add_word("init", SignatureType.operator, "START", 1, [
    TokenClass.num
])
lang_dict.add_word("delay", SignatureType.operator, "ADVANCE", 1, [
    TokenClass.num,
    TokenClass.num
])
lang_dict.add_word("destroy", SignatureType.operator, "TERMINATE", 0, [
    TokenClass.num
])
lang_dict.add_word("goto", SignatureType.operator, "TRANSFER", 1, [
    TokenClass.string
])
lang_dict.add_word("compare", SignatureType.operator, "TEST", 2, [
    TokenClass.word,
    TokenClass.string
])
lang_dict.add_word("changevar", SignatureType.operator, "SAVEVALUE", 1, [
    TokenClass.string
])
lang_dict.add_word("var", SignatureType.operator, "INITIAL", 1, [
    TokenClass.string
])
lang_dict.add_word("copy", SignatureType.operator, "SPLIT", 1, [
    TokenClass.string
])
lang_dict.add_word("link", SignatureType.operator, "LINK", 1, [
    TokenClass.string
])
lang_dict.add_word("unlink", SignatureType.operator, "UNLINK", 1, [
    TokenClass.string
])


temp = []
file: TextIO = open(path, "r")
for row in file:
    if not row.endswith("\n"):
        row += "\n"
    temp.append(lexer.process_line(row))

# Flatten lexer result
result = [item for sublist in temp for item in sublist]
result.append(Token(TokenClass.undefined, ""))
temp.clear()

# Print processed tokens to file
if arguments.lo:
    lexer_output: TextIO = open(path + ".lo", "w")
    for token in result:
        lexer_output.write(str(token) + "\n")
    lexer_output.close()

# Parse tree
parse_tree = ParseTree()
# Symbol table
symbol_table = SymbolTable()

# Process tokens with syntax analyzer
try:
    syntaxer.process_tokens(parse_tree, symbol_table, lang_dict, result)
except SyntaxParseError as error:
    print(error.msg)
    exit(2)
except SemanticError as error:
    print(error.msg)
    exit(2)

# Print processed phrases to file FIXME: TreePrint
if arguments.so:
    syntaxer_output: TextIO = open(path + ".so", "w")
    syntaxer_output.close()

# Code generator
output_file: TextIO = open(path[:-3] + "gpss", "w")
cg = CodeGenerator(parse_tree, lang_dict, output_file)
cg.compile()
output_file.close()
