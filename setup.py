# Licensed under the MIT License
# https://github.com/grongierisc/iris-dollar-list/blob/main/LICENSE

import os

from setuptools import setup


def main():
    # Read the readme for use as the long description
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'README.md'), encoding='utf-8') as readme_file:
        long_description = readme_file.read()

    # Do the setup
    setup(
        name='iris-dollar-list',
        description='iris-dollar-list',
        long_description=long_description,
        long_description_content_type='text/markdown',
        version='0.9.2',
        author='grongier',
        author_email='guillaume.rongier@intersystems.com',
        keywords='iris-dollar-list',
        url='https://github.com/grongierisc/iris-dollar-list',
        license='MIT',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: 3.11',
            'Topic :: Utilities'
        ],
        package_dir={'': 'src'},
        packages=['iris_dollar_list'],
        entry_points={
            'console_scripts': [
                'iris-dollar-list = dollar_list.main:main'
            ]
        }
    )


if __name__ == '__main__':
    main()
