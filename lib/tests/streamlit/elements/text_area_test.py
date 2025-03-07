# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022-2024)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""text_area unit test."""

import re
from unittest.mock import MagicMock, patch

from parameterized import parameterized

import streamlit as st
from streamlit.errors import StreamlitAPIException
from streamlit.proto.LabelVisibilityMessage_pb2 import LabelVisibilityMessage
from streamlit.testing.v1.app_test import AppTest
from tests.delta_generator_test_case import DeltaGeneratorTestCase


class TextAreaTest(DeltaGeneratorTestCase):
    """Test ability to marshall text_area protos."""

    def test_just_label(self):
        """Test that it can be called with no value."""
        st.text_area("the label")

        c = self.get_delta_from_queue().new_element.text_area
        self.assertEqual(c.label, "the label")
        self.assertEqual(
            c.label_visibility.value,
            LabelVisibilityMessage.LabelVisibilityOptions.VISIBLE,
        )
        self.assertEqual(c.default, "")
        self.assertEqual(c.HasField("default"), True)
        self.assertEqual(c.disabled, False)

    def test_just_disabled(self):
        """Test that it can be called with disabled param."""
        st.text_area("the label", disabled=True)

        c = self.get_delta_from_queue().new_element.text_area
        self.assertEqual(c.disabled, True)

    def test_value_types(self):
        """Test that it supports different types of values."""
        arg_values = ["some str", 123, {}, SomeObj()]
        proto_values = ["some str", "123", "{}", ".*SomeObj.*"]

        for arg_value, proto_value in zip(arg_values, proto_values):
            st.text_area("the label", arg_value)

            c = self.get_delta_from_queue().new_element.text_area
            self.assertEqual(c.label, "the label")
            self.assertTrue(re.match(proto_value, c.default))

    def test_none_value(self):
        """Test that it can be called with None as initial value."""
        st.text_area("the label", value=None)

        c = self.get_delta_from_queue().new_element.text_area
        self.assertEqual(c.label, "the label")
        # If a proto property is null, it is not determined by
        # this value, but by the check via the HasField method:
        self.assertEqual(c.default, "")
        self.assertEqual(c.HasField("default"), False)

    def test_height(self):
        """Test that it can be called with height"""
        st.text_area("the label", "", 300)

        c = self.get_delta_from_queue().new_element.text_area
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, "")
        self.assertEqual(c.height, 300)

    def test_invalid_height(self):
        """Test that it raises an error when passed an invalid height"""
        with self.assertRaises(StreamlitAPIException) as e:
            st.text_area("the label", "", height=50)

        self.assertEqual(
            str(e.exception),
            "Invalid height 50px for `st.text_area` - must be at least 68 pixels.",
        )

    def test_placeholder(self):
        """Test that it can be called with placeholder"""
        st.text_area("the label", "", placeholder="testing")

        c = self.get_delta_from_queue().new_element.text_area
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, "")
        self.assertEqual(c.placeholder, "testing")

    def test_outside_form(self):
        """Test that form id is marshalled correctly outside of a form."""

        st.text_area("foo")

        proto = self.get_delta_from_queue().new_element.color_picker
        self.assertEqual(proto.form_id, "")

    @patch("streamlit.runtime.Runtime.exists", MagicMock(return_value=True))
    def test_inside_form(self):
        """Test that form id is marshalled correctly inside of a form."""

        with st.form("form"):
            st.text_area("foo")

        # 2 elements will be created: form block, widget
        self.assertEqual(len(self.get_all_deltas_from_queue()), 2)

        form_proto = self.get_delta_from_queue(0).add_block
        text_area_proto = self.get_delta_from_queue(1).new_element.text_area
        self.assertEqual(text_area_proto.form_id, form_proto.form.form_id)

    def test_inside_column(self):
        """Test that it works correctly inside of a column."""
        col1, col2, col3 = st.columns([2.5, 1.5, 8.3])

        with col1:
            st.text_area("foo")

        all_deltas = self.get_all_deltas_from_queue()

        # 5 elements will be created: 1 horizontal block, 3 columns, 1 widget
        self.assertEqual(len(all_deltas), 5)
        text_area_proto = self.get_delta_from_queue().new_element.text_area

        self.assertEqual(text_area_proto.label, "foo")

    @parameterized.expand(
        [
            ("visible", LabelVisibilityMessage.LabelVisibilityOptions.VISIBLE),
            ("hidden", LabelVisibilityMessage.LabelVisibilityOptions.HIDDEN),
            ("collapsed", LabelVisibilityMessage.LabelVisibilityOptions.COLLAPSED),
        ]
    )
    def test_label_visibility(self, label_visibility_value, proto_value):
        """Test that it can be called with label_visibility param."""
        st.text_area("the label", label_visibility=label_visibility_value)
        c = self.get_delta_from_queue().new_element.text_area
        self.assertEqual(c.label_visibility.value, proto_value)

    def test_label_visibility_wrong_value(self):
        with self.assertRaises(StreamlitAPIException) as e:
            st.text_area("the label", label_visibility="wrong_value")
        self.assertEqual(
            str(e.exception),
            "Unsupported label_visibility option 'wrong_value'. Valid values are "
            "'visible', 'hidden' or 'collapsed'.",
        )

    def test_help_dedents(self):
        """Test that help properly dedents"""
        st.text_area(
            "the label",
            value="TESTING",
            help="""\
        Hello World!
        This is a test


        """,
        )

        c = self.get_delta_from_queue().new_element.text_area
        self.assertEqual(c.label, "the label")
        self.assertEqual(c.default, "TESTING")
        self.assertEqual(
            c.help,
            """Hello World!
This is a test


""",
        )

    def test_shows_cached_widget_replay_warning(self):
        """Test that a warning is shown when this widget is used inside a cached function."""
        st.cache_data(lambda: st.text_area("the label"))()

        # The widget itself is still created, so we need to go back one element more:
        el = self.get_delta_from_queue(-2).new_element.exception
        self.assertEqual(el.type, "CachedWidgetWarning")
        self.assertTrue(el.is_warning)


class SomeObj:
    pass


def test_text_input_interaction():
    """Test interactions with an empty text_area widget."""

    def script():
        import streamlit as st

        st.text_area("the label", value=None)

    at = AppTest.from_function(script).run()
    text_area = at.text_area[0]
    assert text_area.value is None

    # Input a value:
    at = text_area.input("Foo").run()
    text_area = at.text_area[0]
    assert text_area.value == "Foo"

    # # Clear the value
    at = text_area.set_value(None).run()
    text_area = at.text_area[0]
    assert text_area.value is None


def test_None_session_state_value_retained():
    def script():
        import streamlit as st

        if "text_area" not in st.session_state:
            st.session_state["text_area"] = None

        st.text_area("text_area", key="text_area")
        st.button("button")

    at = AppTest.from_function(script).run()
    at = at.button[0].click().run()
    assert at.text_area[0].value is None
