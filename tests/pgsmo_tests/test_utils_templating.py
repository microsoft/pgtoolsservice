# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os.path as path
import unittest
import unittest.mock as mock

import jinja2

import pgsmo.utils as pgsmo_utils


class TestTemplatingUtils(unittest.TestCase):
    # GET_TEMPLATE_ROOT TESTS ##############################################
    def test_get_template_root(self):
        # If: I attempt to get the template root of this file
        root = pgsmo_utils.templating.get_template_root(__file__, 'templates')

        # Then: The output should match what I expected
        expected = path.join(path.dirname(__file__), 'templates')
        self.assertEqual(root, expected)

    # GET_TEMPLATE_PATH TESTS ##############################################
    def test_get_template_path_no_match(self):
        # Setup: Create a mock os walker
        with mock.patch('pgsmo.utils.templating.os.walk', _os_walker, create=True):
            with self.assertRaises(ValueError):
                # If: I attempt to get the path of a template when it does not exist
                # Then: An exception should be thrown
                pgsmo_utils.templating.get_template_path(TEMPLATE_ROOT_NAME, 'doesnotexist.sql', (9, 0, 0))

    def test_get_template_path_default(self):
        # Setup: Create a mock os walker
        with mock.patch('pgsmo.utils.templating.os.walk', _os_walker, create=True):
            # If: I attempt to get a template path when there is not a good version match
            template_path = pgsmo_utils.templating.get_template_path(TEMPLATE_ROOT_NAME, 'template.sql', (8, 1, 0))

            # Then: The template path should point to the default folder
            self.assertEqual(template_path, path.join(TEMPLATE_ROOT_NAME, '+default', 'template.sql'))

    def test_get_template_path_exact_version_match(self):
        # Setup: Create a mock os walker
        with mock.patch('pgsmo.utils.templating.os.walk', _os_walker, create=True):
            # If: I attempt to get the path of a template when there's a exact version match
            template_path = pgsmo_utils.templating.get_template_path(TEMPLATE_ROOT_NAME, 'template.sql', (9, 0, 0))

            # Then: The returned path must match the exact version
            self.assertEqual(template_path, path.join(TEMPLATE_ROOT_NAME, '9.0', 'template.sql'))

    def test_get_template_path_plus_match(self):
        # Setup: Create a mock os walker
        with mock.patch('pgsmo.utils.templating.os.walk', _os_walker, create=True):
            # If: I attempt to get a template path when there is a version range that matches
            template_path = pgsmo_utils.templating.get_template_path(TEMPLATE_ROOT_NAME, 'template.sql', (9, 3, 0))

            # Then: The returned path should match the next lowest version range
            self.assertEqual(template_path, path.join(TEMPLATE_ROOT_NAME, '9.2_plus', 'template.sql'))

    def test_get_template_path_invalid_folder(self):
        # Setup: Create a mock os walker that has an invalid folder in it
        with mock.patch('pgsmo.utils.templating.os.walk', _bad_os_walker, create=True):
            with self.assertRaises(ValueError):
                # If: I attempt to get a template path when there is an invalid folder in the template folder
                # Then: I should get an exception
                pgsmo_utils.templating.get_template_path(TEMPLATE_ROOT_NAME, 'template.sql', (9, 0, 0))

    # RENDER_TEMPLATE TESTS ################################################
    def test_render_template_no_macros(self):
        # NOTE: This test has an external dependency on dummy_template.txt
        # If: I render a string
        template_file = 'dummy_template.txt'
        template_folder = path.dirname(__file__)
        template_path = path.normpath(path.join(template_folder, template_file))
        rendered = pgsmo_utils.templating.render_template(template_path, None, foo='bar')

        # Then:
        # ... The output should be properly rendered
        self.assertEqual(rendered, 'bar')

        # ... The environment should be cached
        self.assertIsInstance(pgsmo_utils.templating.TEMPLATE_ENVIRONMENTS, dict)
        env_hash = pgsmo_utils.templating._hash_source_list([template_folder])
        env = pgsmo_utils.templating.TEMPLATE_ENVIRONMENTS.get(env_hash)
        self.assertIsInstance(env, jinja2.Environment)

        # ... The environment should only have the template folder as a path
        loader = env.loader
        self.assertIsInstance(loader, jinja2.FileSystemLoader)
        self.assertListEqual(loader.searchpath, [template_folder])

        # ... The environment should have the proper filters defined
        self.assertEquals(env.filters['qtLiteral'], pgsmo_utils.templating.qt_literal)
        self.assertEquals(env.filters['qtIdent'], pgsmo_utils.templating.qt_ident)
        self.assertEquals(env.filters['qtTypeIdent'], pgsmo_utils.templating.qt_type_ident)
        self.assertEquals(env.filters['hasAny'], pgsmo_utils.templating.has_any)

    def test_render_template_with_macros(self):
        # NOTE: This test has an external dependency on dummy_template.txt
        # If: I render a string
        template_file = 'dummy_template.txt'
        template_folder = path.dirname(__file__)
        template_path = path.normpath(path.join(template_folder, template_file))
        macro_folder1 = path.normpath(path.dirname(path.dirname(__file__)))
        macro_folder2 = path.normpath(path.dirname(path.dirname(path.dirname(__file__))))
        macro_folders = [macro_folder1, macro_folder2]
        all_folders = [template_folder, macro_folder1, macro_folder2]
        rendered = pgsmo_utils.templating.render_template(template_path, macro_folders, foo='bar')

        # Then:
        # ... The output should be properly rendered
        self.assertEqual(rendered, 'bar')

        # ... The environment should be cached
        self.assertIsInstance(pgsmo_utils.templating.TEMPLATE_ENVIRONMENTS, dict)
        env_hash = pgsmo_utils.templating._hash_source_list(all_folders)
        env = pgsmo_utils.templating.TEMPLATE_ENVIRONMENTS.get(env_hash)
        self.assertIsInstance(env, jinja2.Environment)

        # ... The environment should only have the template folder and macro folders in its path
        loader = env.loader
        self.assertIsInstance(loader, jinja2.FileSystemLoader)
        all_folders = [template_folder, *macro_folders]
        self.assertListEqual(loader.searchpath, all_folders)

        # ... The environment should have the proper filters defined
        self.assertEquals(env.filters['qtLiteral'], pgsmo_utils.templating.qt_literal)
        self.assertEquals(env.filters['qtIdent'], pgsmo_utils.templating.qt_ident)
        self.assertEquals(env.filters['qtTypeIdent'], pgsmo_utils.templating.qt_type_ident)
        self.assertEquals(env.filters['hasAny'], pgsmo_utils.templating.has_any)

    def test_render_template_cached(self):
        # NOTE: This test has an external dependency on dummy_template.txt
        # If:
        # ... I render a string
        template_file = 'dummy_template.txt'
        template_folder = path.dirname(__file__)
        template_path = path.normpath(path.join(template_folder, template_file))
        rendered1 = pgsmo_utils.templating.render_template(template_path, foo='bar')
        env1_hash = pgsmo_utils.templating._hash_source_list([template_folder])
        env1 = pgsmo_utils.templating.TEMPLATE_ENVIRONMENTS.get(env1_hash)

        # ... I render the same string
        rendered2 = pgsmo_utils.templating.render_template(template_path, foo='bar')
        env2_hash = pgsmo_utils.templating._hash_source_list([template_folder])
        env2 = pgsmo_utils.templating.TEMPLATE_ENVIRONMENTS.get(env2_hash)

        # Then: The environments used should be literally the same
        self.assertEqual(rendered1, rendered2)
        self.assertIs(env1, env2)

    def test_render_template_differing_macro(self):
        # NOTE: This test has an external dependency on dummy_template.txt
        # If:
        # ... I render a string
        template_file = 'dummy_template.txt'
        template_folder = path.dirname(__file__)
        template_path = path.normpath(path.join(template_folder, template_file))
        rendered1 = pgsmo_utils.templating.render_template(template_path, foo='bar')
        env1_hash = pgsmo_utils.templating._hash_source_list([template_folder])
        env1 = pgsmo_utils.templating.TEMPLATE_ENVIRONMENTS.get(env1_hash)

        # ... I render the same string
        macro_folder = path.normpath(path.dirname(path.dirname(__file__)))
        all_folders = [template_folder, macro_folder]
        rendered2 = pgsmo_utils.templating.render_template(template_path, [macro_folder], foo='bar')
        env2_hash = pgsmo_utils.templating._hash_source_list(all_folders)
        env2 = pgsmo_utils.templating.TEMPLATE_ENVIRONMENTS.get(env2_hash)

        # Then: The environments used should be different
        self.assertEqual(rendered1, rendered2)
        self.assertIsNot(env1, env2)

    # RENDER_TEMPLATE_STRING TESTS #########################################
    def test_render_template_string(self):
        # NOTE: doing very minimal test here since this function just uses jinja2 functionality
        # If: I render a string
        rendered = pgsmo_utils.templating.render_template_string('{{foo}}', foo='bar')

        # Then: The string should be properly rendered
        self.assertEqual(rendered, 'bar')


# Mock setup for a template tree
TEMPLATE_ROOT_NAME = 'templates'
TEMPLATE_EXACT_1 = (path.join(TEMPLATE_ROOT_NAME, '9.0'), [], ['template.sql'])
TEMPLATE_EXACT_2 = (path.join(TEMPLATE_ROOT_NAME, '9.1'), [], ['template.sql'])
TEMPLATE_PLUS_1 = (path.join(TEMPLATE_ROOT_NAME, '9.2_plus'), [], ['template.sql'])
TEMPLATE_PLUS_2 = (path.join(TEMPLATE_ROOT_NAME, '9.4_plus'), [], ['template.sql'])
TEMPLATE_DEFAULT = (path.join(TEMPLATE_ROOT_NAME, '+default'), [], ['template.sql'])

# Tests that skipped folders are not returned
TEMPLATE_SKIP = (path.join(TEMPLATE_ROOT_NAME, 'macros'), [], ['template.sql'])

# Root tree
TEMPLATE_ROOT = (
    TEMPLATE_ROOT_NAME,
    [
        TEMPLATE_DEFAULT[0],
        TEMPLATE_EXACT_1[0],
        TEMPLATE_EXACT_2[0],
        TEMPLATE_PLUS_1[0],
        TEMPLATE_PLUS_2[0],
        TEMPLATE_SKIP[0]
    ],
    []
)


def _os_walker(x):
    if x == TEMPLATE_ROOT_NAME:
        yield TEMPLATE_ROOT
        yield TEMPLATE_DEFAULT
        yield TEMPLATE_EXACT_1
        yield TEMPLATE_EXACT_2
        yield TEMPLATE_PLUS_1
        yield TEMPLATE_PLUS_2
        yield TEMPLATE_SKIP
    if x == TEMPLATE_DEFAULT[0]:
        yield TEMPLATE_DEFAULT
    if x == TEMPLATE_EXACT_1[0]:
        yield TEMPLATE_EXACT_1
    if x == TEMPLATE_EXACT_2[0]:
        yield TEMPLATE_EXACT_2
    if x == TEMPLATE_PLUS_1[0]:
        yield TEMPLATE_PLUS_1
    if x == TEMPLATE_PLUS_2[0]:
        yield TEMPLATE_PLUS_2
    if x == TEMPLATE_SKIP[0]:
        yield TEMPLATE_SKIP


TEMPLATE_BAD = (path.join(TEMPLATE_ROOT_NAME, 'bad_folder'), [], ['template.sql'])
TEMPLATE_BAD_ROOT = (TEMPLATE_ROOT_NAME, [TEMPLATE_BAD[0]], [])


def _bad_os_walker(x):
    if x == TEMPLATE_ROOT_NAME:
        yield TEMPLATE_BAD_ROOT
        yield TEMPLATE_BAD
    if x == TEMPLATE_BAD[0]:
        yield TEMPLATE_BAD
