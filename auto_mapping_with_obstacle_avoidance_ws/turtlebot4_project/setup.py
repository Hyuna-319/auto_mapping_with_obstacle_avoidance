from setuptools import setup, find_packages

package_name = 'turtlebot4_project'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(where='.', include=[package_name]),  
    install_requires=['setuptools'],
    zip_safe=True,
    author='hyuna',
    author_email='sjajmh6612@naver.com',
    description='TurtleBot4 project for automation tasks',
    license='Apache 2.0',
    entry_points={
        'console_scripts': [
            'automap = turtlebot4_project.automap:main',
            'follow = turtlebot4_project.wall_follow:main',
        ],
    },
)

