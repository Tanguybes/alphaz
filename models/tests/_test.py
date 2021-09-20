import traceback, inspect
from core import core
from typing import List, Dict

import pandas as pd

from ._save import AlphaSave

LOG = core.get_logger("tests")


class AlphaTest:
    _disabled = []
    _test = True
    category = ""

    def __init__(self):
        self.outputs: bool = None
        self.index = 0

    def end(self):
        pass

    def test(self, name):
        self.output = None
        status = False
        fct = getattr(self, name)
        if fct is None:
            LOG.info(
                f"Failed to get testing function <{name}> in category <{self.category}>"
            )
            return False
        try:
            status = fct()
            if self.output is not None:
                status = self.output
        except Exception as ex:
            text = traceback.format_exc()
            LOG.error(text)
        return status

    def save(self, name):
        fct = getattr(self, name)
        if fct is None:
            return False

        if inspect.unwrap(fct).__name__ == save_method_name:  # TODO: modify
            object_to_save = fct(get_return=True)
            object_name_to_save = fct(get_name=True)
            AlphaSave.save(object_to_save, object_name_to_save)

    def reverse(self):
        self.__reverse_output()

    def __reverse_output(self):
        self.output = not self.output
        return self.output

    def _set_output(self, status):
        if self.output is not None:
            self.output = status and self.output
        else:
            self.output = status
        return self.output

    def assert_array_equal(self, a, b, conditions: List[bool] = []) -> bool:
        status = len(a) == len(b)
        if status:
            for i in range(len(a)):
                if a[i] != b[i]:
                    status = False
        if not status:
            LOG.info(f"Assert: <{a}> and <{b}> are not equals")
        return self._assert(status, conditions)

    def _assert(self, status, conditions: List[bool] = []) -> bool:
        if len(conditions) != 0 and type(conditions) == list:
            status = status and all(conditions)
        return self._set_output(status)

    def assert_is_not_none(self, a, conditions: List[bool] = []) -> bool:
        status = a is not None
        if not status:
            LOG.info("Assert: value is None")
        return self._assert(status, conditions)

    def assert_is_empty(self, a, conditions: List[bool] = [], attribute=None) -> bool:
        status = self.assert_is_not_empty(a, conditions=conditions, attribute=attribute)
        if status:
            LOG.info("Assert: value is not empty")
        return self.__reverse_output()

    def assert_are_keys_in_model_attributes(
        self, a, model, attributes=[], conditions: List[bool] = []
    ):
        return self.assert_are_keys_in_models_attributes(
            a, [model], attributes=attributes, conditions=conditions
        )

    def assert_are_keys_in_models_attributes(
        self, a, models, attributes=[], conditions: List[bool] = []
    ):
        self.assert_is_not_none(a)
        for model in models:
            attributes.extend(list(model.get_schema()._declared_fields.keys()))
        attributes = list(set(attributes))
        key_in = {x: x in attributes for x in a.keys()}
        status = all(key_in.values())
        if not status:
            LOG.info(
                f"Assert: missing keys in model: {','.join([x for x, y in key_in.items() if not y])}"
            )
        return self._assert(status, conditions)

    def assert_has_model_attributes(
        self, a, model, conditions: List[bool] = []
    ) -> bool:
        self.assert_is_not_none(a)
        fields = list(model.get_schema()._declared_fields.keys())
        key_in = {x: x in a.keys() for x in fields}
        status = all(key_in.values())
        if not status:
            LOG.info(
                f"Assert: missing model keys: {','.join([x for x, y in key_in.items() if not y])}"
            )
        return self._assert(status, conditions)

    def assert_is_true(self, a, conditions: List[bool] = []):
        status = a
        return self._assert(status, conditions)

    def assert_is_not_empty(
        self, a, conditions: List[bool] = [], attribute=None
    ) -> bool:
        if attribute is not None:
            if not hasattr(a, attribute):
                LOG.info(
                    f"Object of type <{type(a)}> does not have an attribute named <{attribute}>"
                )
            status = a is not None and not len(getattr(a, attribute)) == 0
        elif isinstance(a, pd.DataFrame):
            status = a is not None and not a.empty
        else:
            status = a is not None and len(a) != 0
        if not status:
            LOG.info("Assert: value is None")
        return self._assert(status, conditions)

    def assert_is_dict(self, a, conditions: List[bool] = []):
        status = type(a) == dict
        if not type(a) == dict:
            LOG.info("Assert: value is not a dict")
        return self._assert(status, conditions)

    def assert_is_dict_not_empty(self, a, conditions: List[bool] = []):
        self.assert_is_dict(a)
        status = self.assert_is_not_empty(a)
        return self._assert(status, conditions)

    def assert_is_dict_with_key(self, a, key, conditions: List[bool] = []) -> bool:
        self.assert_is_dict(a)
        status = key in a
        if not status:
            LOG.info(f"Assert: dict has not key {key}")
        return self._assert(status, conditions)

    def assert_is_dict_with_key_not_empty(
        self, a, key, conditions: List[bool] = []
    ) -> bool:
        self.assert_is_not_none(a)
        self.assert_is_dict_with_key(a, key)
        status = self.assert_is_not_empty(a)
        return self._assert(status, conditions)

    def assert_equal(self, a, b, conditions: List[bool] = []) -> bool:
        status = a == b
        if not status:
            LOG.info(f"Assert: {a} and {b} are not equals")
        return self._assert(status, conditions)

    def assert_length(
        self, a, length, conditions: List[bool] = [], strict: bool = False
    ) -> bool:
        status_not_none = self.assert_is_not_none(a)
        status = len(a) == length
        if strict:
            status = status and len(a) != 0
        if not status and status_not_none:
            LOG.info(f"Assert: length {len(a)} is not the {length} expected")
        return self._assert(status, conditions)

    def assert_transaction(self, tr, conditions: List[bool] = []) -> bool:
        status_not_none = self.assert_is_not_none(tr)
        status = tr is not None and tr != "timeout"
        if not status and status_not_none:
            LOG.info(f"Assert: object if not a transaction")
        return self._assert(status, conditions)
