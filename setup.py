from setuptools import find_packages, setup


setup(
    name="foundry-media-pipeline-prototype",
    version="0.1.0",
    description="Prototype for upload -> Foundry analysis -> structured output pipelines",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "pydantic==2.11.7",
        "httpx==0.28.1",
    ],
)
