import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hybrid_routing",
    use_scm_version=False,
    author="Louis Bu",
    description="Smart Shipping Hybrid Routing implementation",
    long_description=long_description,
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    setup_requires=["setuptools_scm"],
    install_requires=[
        "jax==0.2.17",
        "jaxlib==0.3.14",
        "matplotlib==2.1.1",
        "numpy==1.19.5",
        "scipy>=1.0.1",
        "streamlit==1.11.0",
    ],
)
