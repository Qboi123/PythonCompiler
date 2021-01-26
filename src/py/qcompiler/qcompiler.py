import os
import shlex
import shutil
import sys
import traceback
from abc import ABC, abstractmethod
from py_compile import compile
from typing import MutableSequence, Tuple, Iterable, Union, Optional
from zipapp import create_archive

from mypy.api import run


class CompilerError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class QCompiler(ABC):
    def __init__(self):
        pass

    # noinspection PyUnusedFunction
    @abstractmethod
    def compile(self):
        pass

    @staticmethod
    def check_project(path: str):
        run(path)


class QCompilerPYC(QCompiler):
    def __init__(self, exclude: Iterable[str], path: str, clean: bool = True, optimize: int = 2, quiet: bool = False):
        """
        Compiler for compiling python files to Compiled Python (.pyc) files.

        Parameters:
          exclude: An list of relative paths to exclude
          path: The path to be compiled into Compile Python (.pyc) files
          clean: Cleans the output directory
          optimize: An integer, 0 means no optimization, 1 means low level optimization, 2 means high level optimization
          quiet: ...

        Defaults:
          clean: True
          optimize: 2  # High level optimization
          quiet: False  # Don't' suspress the output

        Types:
          exclude: Iterable[str]
          path: str
          clean: bool
          optimize: int
          quiet: bool

        :type quiet: bool
        :type optimize: int
        :type exclude: Iterable[str]
        :type path: str
        """

        super(QCompilerPYC, self).__init__()

        self.clean = clean
        self.quiet = quiet
        self.optimize = optimize
        self.exclude = exclude
        self.path = path
        self.output = os.path.join(os.getcwd(), "bin", "pyc")

    def clean_directory(self, directory):
        for item in os.listdir(directory):
            i_path = os.path.join(directory, item)
            if os.path.isdir(i_path):
                self.clean_directory(i_path)
            else:
                os.remove(i_path)
        os.rmdir(directory)

    def compile_directory(self, directory, to=None):
        if to is None:
            to = os.path.join(self.output, os.path.split(self.path)[-1])
        if not os.path.exists(to):
            os.makedirs(to)
        for item in os.listdir(directory):
            i_path = os.path.join(directory, item)
            t_path = os.path.join(to, item)
            if os.path.isdir(i_path):
                self.compile_directory(i_path, t_path)
            elif os.path.isfile(i_path):
                if os.path.splitext(i_path)[-1] == ".py":
                    self.compile_file(i_path, t_path)
                else:
                    self.copy_file(i_path, t_path)

    @staticmethod
    def copy_file(src, dst):
        shutil.copy2(src, dst)

    def compile_file(self, file, to=None):
        print(f"Compiling '{file}' to {os.path.splitext(to)[0]+'.pyc'}")
        print(compile(file, os.path.splitext(to)[0]+".pyc", optimize=self.optimize))  # , quiet=self.quiet)

    def compile(self):
        self.check_project(self.path)

        if not os.path.exists(self.path):
            os.makedirs(self.path)
        if self.clean:
            self.clean_directory(self.output)
        if os.path.isdir(self.path):
            self.compile_directory(self.path)
        if os.path.isfile(self.path):
            if os.path.splitext(self.path)[-1] == ".py":
                self.compile_file(self.path, to=os.path.join(self.output, os.path.split(self.path)[-1]))


class QCompilerPYD(QCompilerPYC):
    def __init__(self, exclude: Iterable[str], path: str, clean: bool = True, optimize: int = 2, quiet: bool = False):
        """
        Compiler for compiling python files to Python Extension (.pyd) files.

        Parameters:
          exclude: An list of relative paths to exclude
          path: The path to be compiled into Python Extension (.pyd) files
          clean: Cleans the output directory
          optimize: An integer, 0 means no optimization, 1 means low level optimization, 2 means high level optimization
          quiet: ...

        Defaults:
          clean: True
          optimize: 2  # High level optimization
          quiet: False  # Don't' suspress the output

        Types:
          exclude: Iterable[str]
          path: str
          clean: bool
          optimize: int
          quiet: bool

        :type quiet: bool
        :type optimize: int
        :type exclude: Iterable[str]
        :type path: str
        """

        super(QCompilerPYD, self).__init__(exclude, path, clean, optimize, quiet)

        self.output = os.path.join(os.getcwd(), "bin", "pyd")

    def compile_file(self, file, to=None):
        compile(file, dfile=os.path.splitext(to)[0]+".pyd", optimize=self.optimize, quiet=self.quiet)


class QCompilerPYZ(QCompiler):
    def __init__(self, path, name, main_class="Main", compressed=True, compiler: Optional[Union[QCompilerPYC, QCompilerPYD]]=None, clean: bool = True):
        super(QCompilerPYZ, self).__init__()
        self.clean = clean
        self.path = path
        self.name = name
        self.mainClass = main_class
        self.compressed = compressed
        self.compiler = compiler

    def create_archive(self, source, target):
        print(source, target)
        main_class = self.mainClass
        create_archive(source=source, target=target, compressed=self.compressed, main=self.mainClass)

    def clean_directory(self, directory):
        for item in os.listdir(directory):
            i_path = os.path.join(directory, item)
            if os.path.isdir(i_path):
                self.clean_directory(i_path)
            else:
                os.remove(i_path)
        os.rmdir(directory)

    def copy_additional_files(self, src, dst):
        if os.path.isdir(src):
            if not os.path.exists(src):
                os.makedirs(src)
            if not os.path.exists(dst):
                os.makedirs(dst)
            print(f"Found directory: {src}")
            for item in os.listdir(src):
                s_path = os.path.join(src, item)
                d_path = os.path.join(dst, item)
                self.copy_additional_files(s_path, d_path)
        else:
            if not src.endswith(".py"):
                if not src.endswith(".pyc"):
                    if not src.endswith(".pyd"):
                        if not src.endswith(".pyo"):
                            shutil.copy2(src, dst)
                            print(f"Copying {src} to {dst}")

    def compile(self):
        self.check_project(self.path)

        mod_path = self.path.replace('\\', '/')
        while mod_path.endswith("/"):
            mod_path = mod_path[:-1]
        if not os.path.exists("bin/pyz/"):
            os.makedirs("bin/pyz/")

        if self.compiler is None:
            self.create_archive(mod_path, f"bin/pyz/{self.name}")
        else:
            if not os.path.exists("obj/pyz/"):
                os.makedirs("obj/pyz/")
            self.clean_directory("obj/pyz/")
            if type(self.compiler) == QCompilerPYC:
                compilerpath = "bin/pyc"
            elif type(self.compiler) == QCompilerPYD:
                compilerpath = "bin/pyd"
            else:
                raise CompilerError(f"Incompatible compiler: {type(self.compiler).__name__}")
            if not os.path.exists(f"obj/pyz/{compilerpath}"):
                os.makedirs(f"obj/pyz/{compilerpath}")
            self.compiler.output = f"obj/pyz/{compilerpath}"
            self.compiler.compile()
            self.create_archive(f"obj/pyz/{compilerpath}/{os.path.split(self.path)[-1]}", f"bin/pyz/{self.name}")
            self.copy_additional_files(self.path, "bin/pyz/")
            print(f"Compiled to: bin/pyz/{self.name}")


# noinspection PyUnusedClass
class QCompilerEXE(object):
    def __init__(self, exclude: MutableSequence[str], icon: str, main_folder: str, main_file: str,
                 hidden_imports: MutableSequence[str], dlls: MutableSequence[str] = None, one_file=False,
                 hide_console=False, fix_recursion_limit=True, upx_dir: str = None, log_level: str = "INFO",
                 app_name: str = "", extra_binaries: MutableSequence[Tuple[str, str]] = None,
                 import_paths: MutableSequence[str] = None, add_hooks_dirs: MutableSequence[str] = None,
                 runtime_hooks: MutableSequence[str] = None, exclude_modules: MutableSequence[str] = None,
                 key: str = None, debug: str = None, no_unicode=False, clean=False, apply_symbol_table=False,
                 no_upx=False, version_file: str = None, manifest_file: str = None, uac_admin=False, uac_uiaccess=False,
                 win_private_assemblies=False, win_no_prefer_redirects=False, osx_bundle_indentifier: str = None,
                 runtime_tmpdir: str = "", bootloader_ignore_signals=False, *additional_args):
        """
        Compiler class, compiling python workspace.

        :param exclude:
        :param icon:
        :param main_folder:
        :param main_file:
        :param hidden_imports:
        :param dlls:
        :param one_file:
        :param hide_console:
        :param fix_recursion_limit:
        :param upx_dir:
        :param log_level:
        :param app_name:
        :param extra_binaries:
        :param import_paths:
        :param add_hooks_dirs:
        :param runtime_hooks:
        :param exclude_modules:
        :param key:
        :param debug:
        :param no_unicode:
        :param clean:
        :param apply_symbol_table:
        :param no_upx:
        :param version_file:
        :param manifest_file:
        :param uac_admin:
        :param uac_uiaccess:
        :param win_private_assemblies:
        :param win_no_prefer_redirects:
        :param osx_bundle_indentifier:
        :param runtime_tmpdir:
        :param bootloader_ignore_signals:
        :param additional_args:
        """

        # Replace None with the default value
        if hidden_imports is None:
            hidden_imports = list()

        # One File
        self.oneFile = one_file

        # Hide the console
        self.hideConsole = hide_console

        # Internal options
        self.mainFolder = main_folder
        self.mainFile = main_file
        self.mainContents = os.listdir(main_folder)
        self.dllFiles = dlls
        self.exclude = exclude
        self.icon = icon
        self.allFiles = []

        # General Options
        self.upxDirectory = upx_dir
        self.noUnicode = no_unicode
        self.cleanCompile = clean
        self.logLevel = log_level
        self.appName = app_name

        # What to bundle, and where to search
        self.extraBinaries = extra_binaries
        self.importPaths = import_paths
        self.hiddenImports = hidden_imports
        self.additionalHooksDirs = add_hooks_dirs
        self.runtimeHooks = runtime_hooks
        self.excludeModules = exclude_modules
        self.key = key

        # How to generate
        self.debug = debug
        self.applySymbolTable = apply_symbol_table
        self.noUPX = no_upx

        # Windows specific options
        self.versionFile = version_file
        self.manifestFile = manifest_file
        self.requestElevation = uac_admin
        self.remoteDesktop = uac_uiaccess

        # Windows Side-by-side Assembly searching options
        self.privateAssemblies = win_private_assemblies
        self.noPreferRedirects = win_no_prefer_redirects

        # Mac OS X specifiec options
        self.osxBundleIndentifier = osx_bundle_indentifier

        # Rarely used special options
        self.runtimeTempDir = runtime_tmpdir
        self.bootloaderIgnoreSignals = bootloader_ignore_signals

        # Manual Command Entry
        self.additionalArgs = additional_args

        if fix_recursion_limit:
            sys.setrecursionlimit(5000)

        self.check()

    def check(self):
        """
        Check for errors

        :return:
        """
        self.check_project(self.path)

        if self.icon in self.exclude:
            raise CompilerError("Can't exclude icon!")

    def automatic(self):
        """
        Automatic mode

        :return:
        """
        self.reindex()
        args_list = self.get_args()
        command = self.get_command(args_list)

        self.compile(command)

    def get_command(self, args_list):
        """
        Get command for PyInstaller

        :param args_list:
        :return:
        """
        args = self.parse_arg_list(args_list)
        return "pyinstaller " + args

    # noinspection PyBroadException
    def compile(self, command):
        """
        Compile the workspace, with the given command for PyInstaller
        :param command:
        :return:
        """
        from PyInstaller import __main__ as pyi

        # Initialize variables
        temporary_directory = self.join_path(self.mainFolder, "obj")
        output = self.join_path(self.mainFolder, "bin")

        # Notify the user of the workspace and setup building to it
        print("Building in the current instances temporary directory at {}".format(temporary_directory))
        print("To get a new temporary directory, restart this application")
        dist_path = os.path.join(temporary_directory, 'application')
        build_path = os.path.join(temporary_directory, 'build')
        extra_args = ['--distpath', dist_path] + ['--workpath', build_path] + ['--specpath', temporary_directory]

        # Run PyInstaller
        sys.argv = shlex.split(command) + extra_args  # Put command into sys.argv and extra args
        print("Executing: {0}".format(command))
        pyi.run()  # Execute PyInstaller
        print("An error occurred, traceback follows:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)

        # Move project if there was no failure
        output_directory = os.path.abspath(output)  # Use absolute directories
        print("Moving project to: {0}".format(output_directory))
        self.move_project(dist_path, output_directory)
        print("Complete.")

    @staticmethod
    def move_project(src, dst):
        """
        Move the project from <src> to <dst>. Mostly common it moves the project to "./bin"
        :param src:
        :param dst:
        :return:
        """
        """ Move the output package to the desired path (default is output/ - set in script.js) """
        # Make sure the destination exists
        if not os.path.exists(dst):
            os.makedirs(dst)

        # Move all files/folders in dist/
        for file_or_folder in os.listdir(src):
            _dst = os.path.join(dst, file_or_folder)
            # If this already exists in the destination, delete it
            if os.path.exists(_dst):
                if os.path.isfile(_dst):
                    os.remove(_dst)
                else:
                    shutil.rmtree(_dst)
            # Move file
            shutil.move(os.path.join(src, file_or_folder), dst)

    @staticmethod
    def join_path(path, *paths):
        """
        Joins path using the "os" package, then replaces every "\" with "/"
        :param path:
        :param paths:
        :return:
        """
        return os.path.join(path, *paths).replace("\\", "/")

    def _reindex_relpath(self, folder):
        """
        Reindex's the relative path to <folder>
        :param folder:
        :return:
        """
        for export_path in os.listdir(self.join_path(self.mainFolder, folder)):
            export_path = self.join_path(folder, export_path)
            path = self.join_path(self.mainFolder, export_path)
            if export_path in self.exclude:
                continue
            if export_path not in ["bin", "obj", "__pycache__", self.mainFile]:
                if os.path.split(export_path)[-1] not in ["__pycache__"]:
                    if os.path.isfile(path):
                        print("Indexed File: (%s, %s)" % (path, os.path.join(*os.path.split(export_path)[:-1])))
                        self.allFiles.append((path, os.path.join(*os.path.split(export_path)[:-1])))
                    if os.path.isdir(path):
                        print("Indexed Folder: %s" % export_path)
                        self._reindex_relpath(export_path)

    def reindex(self):
        """
        Reindex all files in the workspace
        :return:
        """
        self.allFiles = []
        for export_path in self.mainContents:
            path = self.join_path(self.mainFolder, export_path)
            if export_path in self.exclude:
                continue
            if export_path not in ["bin", "obj", "__pycache__", self.mainFile]:
                if os.path.isfile(path):
                    print("Indexed File: (%s, %s)" % (path, "."))
                    self.allFiles.append((path, "."))
                if os.path.isdir(path):
                    print("Indexed Folder: %s" % export_path)
                    self._reindex_relpath(export_path)

    def get_args(self) -> list:
        """
        Get arguments for the PyInstaller command
        :return:
        """
        args = ["-y"]
        if self.oneFile:
            args.append("-F")
        if self.hideConsole:
            args.append("-w")
        if self.icon:
            args.append("-i \"%s\"" % self.join_path(self.mainFolder, self.icon))
        print("All Files: %s" % self.allFiles)
        for file_location, exported_location in self.allFiles:
            args.append("--add-data \"%s\";\"%s\"" % (file_location.replace("\\", "/"), exported_location))
            print("--add-data \"%s\";\"%s\"" % (file_location.replace("\\", "/"), exported_location))
        if self.dllFiles:
            for file in self.dllFiles:
                args.append("--add-data \"%s\";\".\"" % self.join_path(self.mainFolder, file.replace("\\", "/")))
        if self.upxDirectory:
            args.append("--upx-dir \"%s\"" % self.upxDirectory)
        if self.noUnicode:
            args.append("-a")
        if self.cleanCompile:
            args.append("--clean")
        if self.logLevel:
            args.append("--log-level %s" % self.logLevel.upper())
        if self.appName:
            args.append("-n \"%s\"" % self.appName)
        if self.extraBinaries:
            for src, dist in self.extraBinaries:
                args.append("--add-binary \"%s\";\"%s\"" % (src, dist))
        if self.importPaths:
            for path in self.importPaths:
                args.append("-p %s" % path)
        if self.hiddenImports:
            for hidden_import in self.hiddenImports:
                args.append("--hidden-import \"%s\"" % hidden_import)
        if self.additionalHooksDirs:
            for hooks_dir in self.additionalHooksDirs:
                args.append("--additional-hooks-dir \"%s\"" % hooks_dir)
        if self.runtimeHooks:
            for runtime_hook in self.runtimeHooks:
                args.append("--runtime-hook \"%s\"" % runtime_hook)
        if self.excludeModules:
            for exclude in self.excludeModules:
                args.append("--exclude-module \"%s\"" % exclude)
        if self.key:
            args.append("--key \"%s\"" % self.key)
        if self.debug:
            args.append("--debug \"%s\"" % self.debug)
        if self.applySymbolTable:
            args.append("-s")
        if self.noUPX:
            args.append("--noupx")
        if self.versionFile:
            args.append("--version-file \"%s\"" % self.versionFile)
        if self.manifestFile:
            args.append("-m \"%s\"" % self.manifestFile)
        if self.requestElevation:
            args.append("--uac-admin")
        if self.remoteDesktop:
            args.append("--uac-uiaccess")
        if self.privateAssemblies:
            args.append("--win-private-assemblies")
        if self.noPreferRedirects:
            args.append("--win-no-prefer-redirects")
        if self.osxBundleIndentifier:
            args.append("--osx-bundle-identifier \"%s\"" % self.osxBundleIndentifier)
        if self.runtimeTempDir:
            args.append("--runtime-tmpdir \"%s\"" % self.runtimeTempDir)
        if self.bootloaderIgnoreSignals:
            args.append("--bootloader-ignore-signals")
        args.append(" \"%s\"" % self.join_path(self.mainFolder, self.mainFile))

        return args

    @staticmethod
    def parse_arg_list(args_list):
        """
        Parses a list of arguments into a string
        :param args_list:
        :return:
        """
        args = args_list[0]

        if len(args_list) > 1:
            for arg in args_list:
                args += " " + arg

        return args


class MultiCompiler(QCompilerEXE):
    def __init__(self, compiler: QCompilerEXE, *compilers: QCompilerEXE, appname: str = ""):
        super(QCompilerEXE, self).__init__()
        compilers = list(compilers)
        compilers.append(compiler)

        _temp_appnames = [appname]
        _temp_mainfiles = []
        binfolders = []
        for compiler in compilers:
            if compiler.oneFile:
                error = ValueError(f"Compiler with mainfile '{compiler.mainFile}' is in one-file mode, and one-file "
                                   f"mode is not supported in MultiCompiler")
                error.args = [*error.args, compiler.mainFile]
                raise error
            if compiler.appName in _temp_appnames:
                raise ValueError(f"A compiler with app name '{compiler.appName}' already exists")
            _temp_appnames.append(compiler.appName)
            _temp_mainfiles.append(compiler.mainFile)
            if compiler.appName is None:
                binfolders.append(os.path.splitext(compiler.mainFile)[0])
            else:
                binfolders.append(compiler.appName)

        maindir = os.getcwd()

        for compiler in compilers:
            os.chdir(compiler.mainFolder)
            excludes = [os.path.abspath(exclude) for exclude in compiler.exclude]
            for file in _temp_mainfiles:
                if os.path.abspath(file) not in excludes:
                    compiler.exclude.append(file)
            os.chdir(maindir)

        self.appName = appname
        self.binFolders = binfolders
        self.compilers = compilers

    def compile(self, commands):
        for compiler in self.compilers:
            compiler.compile(compiler.get_command(compiler.get_args()))
        for folder in self.binFolders:
            for inner_folder in os.listdir(folder):
                os.rename(f"bin/{folder}/{inner_folder}", f"bin/{self.appName}/{inner_folder}")
