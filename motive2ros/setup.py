from setuptools import find_packages, setup

package_name = 'motive2ros'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    py_modules=[],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='optimalx',
    maintainer_email='fox00330@umn.edu',
    description='Takes motive data over the internet and creates a ROS node usable for UAV autopilot control.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'talker = motive2ros.publisher_member_function:main',
            'listener = motive2ros.subscriber_member_function:main',
            'datastream = motive2ros.natnet_connector:main',
            'locpub = motive2ros.location_publisher:main',
            'loclist = motive2ros.drone_controller:main',
        ],
    },
)
