from setuptools import setup, find_packages

setup(
    name='vital-ai-vitalsigns',
    version='0.1.19',
    author='Marc Hadfield',
    author_email='marc@vital.ai',
    description='VitalSigns knowledge graph bindings',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/vital-ai/vital-vitalsigns-python',
    packages=find_packages(exclude=["test", "utils", "config", "generate", "vital_home_test"]),
    entry_points={
        'vitalsigns_packages': [
            'vital_ai_vitalsigns = vital_ai_vitalsigns',
            'vital_ai_vitalsigns_core = vital_ai_vitalsigns_core'
        ]
    },
    scripts=['bin/vitalsigns', 'bin/vitalsigns_python'],
    package_data={
        '': ['*.pyi'],
        'vital_ai_vitalsigns': ['models/**'],
    },
    license='Apache License 2.0',
    install_requires=[
        'rdflib==7.0.0',
        'PyYAML',
        'numpy>=1.26.4',
        'hnswlib',
        'owlready2==0.46',
        'owlrl==6.0.2',
        'weaviate-client==4.6.3',
        'SPARQLWrapper==2.0.0',
        'pyshacl==0.25.0',
        'requests',
        # for odbc connection
        'PyODBC>=5.1.0',
        'onnxruntime>=1.18.0',
        'onnx>=1.16.1',
        'tzdata>=2024.1',
        'pytz>=2024.1',
        'python-dotenv>=1.0.1',
        'python-dateutil>=2.9.0',
        'transformers>=4.37.2'
    ],
    extras_require={
        'dev': [
            'torch>=2.3.0',
            'sentence_transformers==2.7.0',
            'wheel>=0.43.0'
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)
