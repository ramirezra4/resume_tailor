from setuptools import setup, find_packages

setup(
    name="resume_tailor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.21.0",
    ],
    entry_points={
        "console_scripts": [
            "resume_tailor=resume_tailor:main",
        ],
    },
    author="ramirezra4",
    author_email="your.email@example.com",
    description="A tool that tailors your LaTeX resume to specific job descriptions using AI",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ramirezra4/resume_tailor",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
