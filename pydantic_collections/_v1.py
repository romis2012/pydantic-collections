import functools
import warnings
from typing import Optional, List, MutableSequence, Type, TypeVar, Any, Callable, TYPE_CHECKING

from pydantic import BaseModel, BaseConfig, ValidationError
from pydantic.error_wrappers import ErrorWrapper
from pydantic.errors import ArbitraryTypeError
from pydantic.fields import ModelField, Undefined

# noinspection PyProtectedMember
from pydantic.main import Extra


class CollectionModelConfig(BaseConfig):
    validate_assignment_strict = False


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


TElement = TypeVar('TElement')


class BaseCollectionModel(BaseModel, MutableSequence[TElement]):
    if TYPE_CHECKING:  # pragma: no cover
        __el_field__: ModelField
        __config__: Type[CollectionModelConfig]
        __root__: List[TElement]

    class Config(CollectionModelConfig):
        extra = Extra.forbid
        validate_assignment = True
        validate_assignment_strict = True

    @tp_cache
    def __class_getitem__(cls, el_type):
        if not issubclass(cls, BaseCollectionModel):
            raise TypeError('{!r} is not a BaseCollectionModel'.format(cls))  # pragma: no cover

        return type(
            '{}[{}]'.format(cls.__name__, el_type),
            (cls,),
            {
                '__el_field__': ModelField.infer(
                    name='{}[{}]:element'.format(cls.__name__, el_type),
                    annotation=el_type,
                    value=Undefined,
                    class_validators=None,
                    config=BaseConfig,
                    # model_config=cls.__config__,
                ),
                '__annotations__': {'__root__': List[el_type]},
            },
        )

    def __init__(self, data: list = None, **kwargs):
        __root__ = kwargs.get('__root__')
        if __root__ is None:
            if data is None:
                __root__ = []
            else:
                __root__ = data

        super(BaseCollectionModel, self).__init__(__root__=__root__)

    def _validate_element(self, value, index):
        if not self.__config__.validate_assignment:
            return value  # pragma: no cover

        if self.__config__.validate_assignment_strict:
            if self.__el_field__.allow_none and value is None:
                pass  # pragma: no cover
            else:
                self._validate_element_type(self.__el_field__, value, index)

        value, err = self.__el_field__.validate(
            value,
            {},
            loc='{} -> {}'.format('__root__', index),
            cls=self.__class__,
        )

        errors = []
        if isinstance(err, ErrorWrapper):
            errors.append(err)
        elif isinstance(err, list):  # pragma: no cover
            errors.extend(err)

        if errors:
            raise ValidationError(errors, self.__class__)

        return value

    def _validate_element_type(self, field: ModelField, value: Any, index: int):
        def get_field_types(fld: ModelField):
            if fld.sub_fields:
                for sub_field in fld.sub_fields:
                    yield from get_field_types(sub_field)
            else:
                yield fld.type_

        if not isinstance(value, tuple(get_field_types(field))):
            error = ArbitraryTypeError(expected_arbitrary_type=field.type_)
            raise ValidationError(
                [ErrorWrapper(exc=error, loc='{} -> {}'.format('__root__', index))],
                self.__class__,
            )

    def __len__(self):
        return len(self.__root__)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self.__class__(self.__root__[index])
        else:
            return self.__root__[index]

    def __setitem__(self, index, value):
        self.__root__[index] = self._validate_element(value, index)
        return self.__root__[index]

    def __delitem__(self, index):
        del self.__root__[index]

    def __iter__(self) -> List[TElement]:
        yield from self.__root__

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.__root__)  # pragma: no cover

    def __str__(self):
        return repr(self)  # pragma: no cover

    def insert(self, index, value):
        self.__root__.insert(index, self._validate_element(value, index))

    def append(self, value):
        index = len(self.__root__) + 1
        self.__root__.append(self._validate_element(value, index))

    def sort(self, key, reverse=False):
        data = sorted(self.__root__, key=key, reverse=reverse)
        return self.__class__(data)

    def dict(
        self,
        *,
        by_alias=False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        **kwargs,
    ) -> List[TElement]:
        data = super().dict(
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        # Original pydantic dict(...) returns a dict of the form {'__root__': [...]}
        # this behavior will be change in ver 2.0
        # https://github.com/samuelcolvin/pydantic/issues/1193
        if isinstance(data, dict):
            return data['__root__']
        else:
            return data  # noqa; #pragma: no cover

    def json(
        self,
        *,
        include=None,
        exclude=None,
        by_alias=False,
        skip_defaults=None,
        exclude_unset=False,
        exclude_defaults=False,
        exclude_none=False,
        encoder: Optional[Callable[[Any], Any]] = None,
        **dumps_kwargs: Any,
    ) -> str:
        if skip_defaults is not None:  # pragma: no cover
            warnings.warn(
                f'{self.__class__.__name__}.json(): "skip_defaults" is deprecated '
                'and replaced by "exclude_unset"',
                DeprecationWarning,
            )
            exclude_unset = skip_defaults

        data = self.dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

        encoder = encoder or self.__json_encoder__
        return self.__config__.json_dumps(data, default=encoder, **dumps_kwargs)
