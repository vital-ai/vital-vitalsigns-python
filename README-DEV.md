
for development:

install vitalsigns in editing mode

pip install -e .

install domains that were previously generated with vitalsigns that are used in tests
currently this includes the KG domain

potentially don't use no-deps as domains that extend other domains should be included
we don't want to re-install vitalsigns but installing that directly in editable model should handle that

pip install --no-deps -r dev-requirements.txt

tests in "test" may use the domains installed via dev-requirements.

tests in "test_generate" are meant to only test domain generation and not be dependent on domains generated
by vitalsigns.  generation should just be dependent on the core model classes.  there is the corner case
of generating a domain that is dependent on other domains beyond the core model and vital model to make sure the dependency
is specified properly in the setup.py for the generated domain.


