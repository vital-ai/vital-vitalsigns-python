from setuptools import setup, find_packages

setup(
    name='vital-ai-vitalsigns',
    version='0.1.12',
    author='Marc Hadfield',
    author_email='marc@vital.ai',
    description='VitalSigns knowledge graph bindings',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/vital-ai/vital-vitalsigns-python',
    packages=find_packages(exclude=["test", "utils", "generate", "vital_home_test"]),
    entry_points={
        'vitalsigns_packages': [
            'vital_ai_vitalsigns = vital_ai_vitalsigns',
            'vital_ai_vitalsigns_core = vital_ai_vitalsigns_core'
        ]
    },
    scripts=['bin/vitalsigns', 'bin/vitalsigns_python'],
    package_data={
         '': ['*.pyi'],
    },
    license='Apache License 2.0',
    install_requires=[
        'sentence_transformers==2.7.0',
        'rdflib==7.0.0',
        'PyYAML',
        'numpy>=1.26.4',
        'hnswlib',
        'owlready2==0.46',
        'owlrl==6.0.2',
        'weaviate-client==4.5.6',
        'SPARQLWrapper==2.0.0',
        'pyshacl==0.25.0',
    ],
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)
