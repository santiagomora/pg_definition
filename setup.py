from distutils.command.install_data import install_data
from setuptools import find_packages, setup, Extension
from setuptools.command.build_ext import build_ext
from setuptools.command.install_lib import install_lib
# from setuptools.command.install_scripts import install_scripts
# from setuptools.command.install import install
import struct
import sys
import pathlib
import os
import shutil
import glob


BITS = struct.calcsize("P") * 8
PACKAGE_NAME = "core_pg_bindings"
PYTHON_VERSION = "3.12"
INCLUDE_DEST = os.path.join(sys.prefix, 'include',  f'python{PYTHON_VERSION}', 'sgs')


class CMakeExtension(Extension):
    """
    An extension to run the cmake build

    This simply overrides the base extension class so that setuptools
    doesn't try to build your sources for you
    """

    def __init__(
        self, *, name: str, cmake_lists_path: list[str], so_destination_path: str,
        include_files_destination_path: str
    ):
        super().__init__(name=name, sources=[])
        self.cmake_lists_path = cmake_lists_path
        self.so_destination_path = so_destination_path
        self.include_files_destination_path = include_files_destination_path


cmake_extensions = [
    CMakeExtension(
        name='libcore_pg_bindings',
        cmake_lists_path=os.path.join(PACKAGE_NAME, 'cpp', 'lib'),
        so_destination_path=os.path.join(sys.prefix, 'lib',  f'python{PYTHON_VERSION}', 'sgs'),
        include_files_destination_path=os.path.join(sys.prefix, 'include', f'python{PYTHON_VERSION}', 'sgs')
    ),
    CMakeExtension(
        name='wrapper',
        cmake_lists_path=os.path.join(PACKAGE_NAME, 'cpp', 'module'),
        so_destination_path=os.path.join(PACKAGE_NAME, 'cpp', 'module'),
        include_files_destination_path=os.path.join(sys.prefix, 'include',  f'python{PYTHON_VERSION}', 'sgs')
    )
]


HEADERS = []


class BuildCMakeExt(build_ext):
    """
    Builds using cmake instead of the python setuptools implicit build
    """

    def run(self):
        """
        Perform build_cmake before doing the 'normal' stuff
        """
        for extension in self.extensions:
            print(f"[BUILD] \"{extension.name}\": Building", file=sys.stdout)
            self.build_cmake(extension)
            self.distribution.extension = extension
            self.run_command('install_lib')

    def build_cmake(self, extension: Extension):
        """
        The steps required to build the extension
        """
        print(f"[BUILD] \"{extension.name}\": Preparing the build environment", file=sys.stdout)
        build_dir = pathlib.Path(self.build_temp)
        extension_path = pathlib.Path(self.get_ext_fullpath(extension.name))
        os.makedirs(build_dir, exist_ok=True)
        os.makedirs(extension_path.parent.absolute(), exist_ok=True)
        # Now that the necessary directories are created, build
        print(f"[BUILD] \"{extension.name}\": Configuring cmake project", file=sys.stdout)
        # Change your cmake arguments below as necessary
        # Below is just an example set of arguments for building Blender as a Python module
        self.spawn(['cmake', f'-H{extension.cmake_lists_path}', f'-B{extension_path}'])
        print(f"[BUILD] \"{extension.name}\": Building libraries", file=sys.stdout)
        self.spawn(["cmake", "--build", extension_path])
        # Build finished, now copy the files into the copy directory
        # We need to move the so files to the final destination
        libs = [
            so for so in
            os.listdir(extension_path) if
            os.path.isfile(os.path.join(extension_path, so)) and
            so.split('.')[-1] == "so"
        ]
        for lib in libs:
            p = os.path.join(build_dir, lib)
            dst = os.path.join(extension_path, lib)
            if os.path.exists(p):
                os.remove(p)
            shutil.move(dst, p)
            print(f"[BUILD] \"{extension.name}\": Moved \"{dst}\" -> \"{build_dir}\"", file=sys.stdout)
        # self.distribution.lib_dir = build_dir
        print(f"[BUILD] \"{extension.name}\": Removing \"{extension_path}\"", file=sys.stdout)
        shutil.rmtree(extension_path)
        # After build_ext is run, the following commands will run:
        # install_lib
        # install_scripts


class InstallCMakeLibs(install_lib):
    """
    Get the libraries from the parent distribution, use those as the outfiles

    Skip building anything; everything is already built, forward libraries to
    the installation step
    """

    def run(self):
        """
        Copy libraries from the bin directory and place them as appropriate
        """
        extension = self.distribution.extension
        print(f"[INSTALL_LIBS] \"{extension.name}\": Installing library", file=sys.stdout)
        # We have already built the libraries in the previous build_ext step
        self.skip_build = True
        build_dir = pathlib.Path(self.get_finalized_command('build').build_temp)
        lib_dir = self.get_finalized_command('build').build_lib
        print(f"[INSTALL_LIBS] \"{extension.name}\": Getting libraries from \"{build_dir}\"", file=sys.stdout)
        # Depending on the files that are generated from your cmake
        # build chain, you may need to change the below code, such that
        # your files are moved to the appropriate location when the installation
        # is run
        install_files = []
        extensions = []
        for lib in os.listdir(build_dir):
            for ext in cmake_extensions:
                if lib.startswith(ext.name):
                    extensions.append((lib, ext, ))
        for libname, ext in extensions:
            os.makedirs(ext.so_destination_path, exist_ok=True)
            final_path = ''
            dest_path = ''
            if os.path.isabs(ext.so_destination_path):
                final_path = os.path.join(ext.so_destination_path, libname)
                # its a so library
                if os.path.exists(final_path):
                    os.remove(final_path)
                dest_path = os.path.join(build_dir, libname)
                shutil.move(dest_path, final_path)
            else:
                # its a compiled c++ wrapper
                final_path = os.path.join(lib_dir, ext.so_destination_path)
                os.makedirs(final_path, exist_ok=True)
                final_path = os.path.join(final_path, libname)
                dest_path = os.path.join(build_dir, libname)
                shutil.move(dest_path, final_path)
            install_files.append(final_path)
            include_path = os.path.join(os.path.join(lib_dir, ext.cmake_lists_path), 'include')
            if os.path.exists(include_path):
                print(f"[INSTALL_LIBS] \"{ext.name}\": Copying \"{include_path}\" contents into \"{INCLUDE_DEST}\"", file=sys.stdout)
                for filename in glob.iglob(include_path + '/**/*', recursive=True):
                    dst = filename.replace(include_path, INCLUDE_DEST)
                    if os.path.isdir(filename):
                        os.makedirs(dst, exist_ok=True)
                    else:
                        HEADERS.append(os.path.abspath(dst))
                        shutil.copy(filename, dst)
                shutil.rmtree(include_path, ignore_errors=True)
            print(f"[INSTALL_LIBS] \"{ext.name}\": Moved \"{dest_path}\" -> \"{final_path}\"", file=sys.stdout)
        # Mark the libs for installation, adding them to 
        # distribution.data_files seems to ensure that setuptools' record 
        # writer appends them to installed-files.txt in the package's egg-info
        # shutil.rmtree(build_dir, ignore_errors=True)
        print(f"[INSTALL_LIBS] \"{self.distribution.extension.name}\": Registering install files", file=sys.stdout)
        self.distribution.data_files = install_files + HEADERS
        # Must be forced to run after adding the libs to data_files
        self.distribution.run_command("install_data")
        super().run()


class InstallCMakeLibsData(install_data):
    """
    Just a wrapper to get the install data into the egg-info

    Listing the installed files in the egg-info guarantees that
    all of the package files will be uninstalled when the user
    uninstalls your package through pip
    """

    def run(self):
        """
        Outfiles are the libraries that were built using cmake
        """
        self.skip_build = True
        extension = self.distribution.extension
        print(f"[INSTALL_DATA] \"{extension.name}\": Registering outfiles", file=sys.stdout)
        self.outfiles += self.distribution.data_files


# class InstallCMakeScripts(install_scripts):
#     """
#     Install the scripts in the build dir
#     """
# 
#     def run(self):
#         """
#         Copy the required directory to the build directory and super().run()
#         """
# 
#         self.announce("Moving scripts files", level=3)
# 
#         # Scripts were already built in a previous step
# 
#         self.skip_build = True
# 
#         bin_dir = self.distribution.bin_dir
# 
#         scripts_dirs = [os.path.join(bin_dir, _dir) for _dir in
#                         os.listdir(bin_dir) if
#                         os.path.isdir(os.path.join(bin_dir, _dir))]
# 
#         for scripts_dir in scripts_dirs:
# 
#             shutil.move(scripts_dir,
#                         os.path.join(self.build_dir,
#                                      os.path.basename(scripts_dir)))
# 
#         # Mark the scripts for installation, adding them to 
#         # distribution.scripts seems to ensure that the setuptools' record 
#         # writer appends them to installed-files.txt in the package's egg-info
# 
#         self.distribution.scripts = scripts_dirs
# 
# #         super().run()


setup(
    packages=find_packages(),
    ext_modules=cmake_extensions,
    data_files=HEADERS,
    cmdclass={
        'build_ext': BuildCMakeExt,
        'install_lib': InstallCMakeLibs,
        'install_data': InstallCMakeLibsData,
        # 'install_scripts': InstallCMakeScripts,
    },
    include_package_data=True
)
