from qcompiler import QCompilerPYZ, QCompilerPYC


pre_compiler = QCompilerPYC([], "TestProgram")
compiler = QCompilerPYZ("TestProgram", "TestProgram.pyz", "__init__:main", False, pre_compiler, True)
compiler.compile()
