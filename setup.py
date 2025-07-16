from setuptools import find_packages, setup
from core_cpp_packaging_tools.setup_script import\
    get_install_cmake_headers,\
    get_install_cmake_libs,\
    get_build_cmake_ext,\
    get_module_packaging_configuration,\
    CPPPackageConfiguration
from core_cpp_packaging_tools.extension import\
    CMakeExtension
import os


setup_config: CPPPackageConfiguration = get_module_packaging_configuration('core_pg_bindings')


setup(
    packages=find_packages(),
    ext_modules=[
        CMakeExtension(
            name='libcore_pg_bindings',
            src_path=setup_config.SRC_PATH,
            cmake_lists_path=os.path.join(setup_config.PACKAGE_CPP_NAME, 'lib'),
            so_destination_path=os.path.join('lib',  f'python{setup_config.PYTHON_VERSION}', 'sgs'),
            include_files_path=(
                os.path.join(setup_config.PACKAGE_CPP_NAME, 'lib', 'include'),
                os.path.join('include', f'python{setup_config.PYTHON_VERSION}')
            ),
            is_package=False
        ),
        CMakeExtension(
            name='wrapper',
            src_path=setup_config.SRC_PATH,
            cmake_lists_path=os.path.join(setup_config.PACKAGE_CPP_NAME, 'module'),
            so_destination_path=os.path.join(setup_config.PACKAGE_NAME, 'cpp'),
            include_files_path=None,
            is_package=True
        )
    ],
    cmdclass={
        'build_ext': get_install_cmake_headers(setup_config),
        'install_lib': get_install_cmake_libs(setup_config),
        'install_data': get_build_cmake_ext(setup_config),
        # 'install_scripts': InstallCMakeScripts,
    },
    include_package_data=True
)
