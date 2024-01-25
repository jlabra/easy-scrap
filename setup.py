from setuptools import find_packages, setup

setup(
    name="dagster_easyscraptracker",
    packages=find_packages(exclude=["dagster_easyscraptracker_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud"
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
