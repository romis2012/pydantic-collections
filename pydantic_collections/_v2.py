import functools
import types
from dataclasses import dataclass
from typing import (
    List,
    TYPE_CHECKING,
    Any,
    Tuple,
    Union,
    Dict,
    TypeVar,
    MutableSequence,
)

from pydantic import RootModel, TypeAdapter, ConfigDict, ValidationError
from pydantic_core import PydanticUndefined, ErrorDetails
from typing_extensions import get_origin, get_args

UnionType = getattr(types, 'UnionType', Union)


def get_types_from_annotation(tp: Any):
    origin = get_origin(tp)
    if origin is Union or origin is UnionType:
        for sub_tp in get_args(tp):
            yield from get_types_from_annotation(sub_tp)
    elif isinstance(tp, type):
        yield tp
    else:
        yield origin


def wrap_errors_with_loc(
    *,
    errors: List[ErrorDetails],
    loc_prefix: Tuple[Union[str, int], ...],
) -> List[Dict[str, Any]]:
    return [{**err, 'loc': loc_prefix + err.get('loc', ())} for err in errors]


def tp_cache(func):
    """Internal wrapper caching __getitem__ of generic types with a fallback to
    original function for non-hashable arguments.
    """
    cached = functools.lru_cache(maxsize=None, typed=True)(func)

    @functools.wraps(func)
    def inner(*args, **kwargs):
        try:
            return cached(*args, **kwargs)
        except TypeError:  # pragma: no cover
            pass  # All real errors (not unhashable args) are raised below.
        return func(*args, **kwargs)  # pragma: no cover

    return inner


class CollectionModelConfig(ConfigDict):
    validate_assignment_strict: bool


@dataclass
class Element:
    annotation: Any
    adapter: TypeAdapter


TElement = TypeVar("TElement")


class BaseCollectionModel(MutableSequence[TElement], RootModel[List[TElement]]):
    if TYPE_CHECKING:  # pragma: no cover
        __element__: Element

    # noinspection Pydantic
    model_config = CollectionModelConfig(
        validate_assignment=True,
        validate_assignment_strict=True,
    )

    @tp_cache
    def __class_getitem__(cls, el_type):
        if not issubclass(cls, BaseCollectionModel):
            raise TypeError('{!r} is not a BaseCollectionModel'.format(cls))  # pragma: no cover

        element = Element(annotation=el_type, adapter=TypeAdapter(el_type))
        return type(
            '{}[{}]'.format(cls.__name__, el_type),
            (cls,),
            {
                '__element__': element,
                '__annotations__': {'root': List[el_type]},
            },
        )

    def __init__(self, data: list = None, root=PydanticUndefined, **kwargs):
        if root is PydanticUndefined:
            if data is None:
                root = []
            else:
                root = data

        super(BaseCollectionModel, self).__init__(root=root, **kwargs)

    def _validate_element_type(self, value: Any, index: int):
        tps = get_types_from_annotation(self.__element__.annotation)
        if not isinstance(value, tuple(tps)):
            error = {
                'type': 'is_instance_of',
                'loc': (index,),
                'input': value,
                'ctx': {'class': str(self.__element__.annotation)},
            }
            raise ValidationError.from_exception_data(
                title=self.__class__.__name__,
                line_errors=[error],
            )

    def _validate_element(self, value: Any, index: int):
        if not self.model_config['validate_assignment']:
            return value

        strict = False
        if self.model_config['validate_assignment_strict']:
            self._validate_element_type(value, index)
            strict = True

        try:
            return self.__element__.adapter.validate_python(
                value,
                strict=strict,
                from_attributes=True,
            )
        except ValidationError as e:
            errors = wrap_errors_with_loc(
                errors=e.errors(),
                loc_prefix=(index,),
            )
            raise ValidationError.from_exception_data(
                title=self.__class__.__name__,
                line_errors=errors,
            )

    def __len__(self):
        return len(self.root)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self.__class__(self.root[index])
        else:
            return self.root[index]

    def __setitem__(self, index, value):
        self.root[index] = self._validate_element(value, index)
        return self.root[index]

    def __delitem__(self, index):
        del self.root[index]

    def __iter__(self):
        yield from self.root

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.root)  # pragma: no cover

    def __str__(self):
        return repr(self)  # pragma: no cover

    def insert(self, index, value):
        self.root.insert(index, self._validate_element(value, index))

    def append(self, value):
        index = len(self.root) + 1
        self.root.append(self._validate_element(value, index))

    def sort(self, key, reverse=False):
        data = sorted(self.root, key=key, reverse=reverse)
        return self.__class__(data)
