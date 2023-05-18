import importlib
import uuid
from datetime import datetime
from distutils import util
from math import ceil
from typing import Any, List, Union

import sqlalchemy
from sqlalchemy import Boolean, DateTime, Float, Integer, String, and_, cast, func, inspect, or_, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, QueryableAttribute
from sqlalchemy.sql import ColumnElement, Select, expression
from sqlalchemy.sql.elements import UnaryExpression


class FilteredListDAOMixin:
    """Mixin for filtered / paginated list on DAO classes."""

    OPERATOR_EQUALS = '='
    OPERATOR_GREATER_THAN = '>'
    OPERATOR_GREATER_OR_EQUALS_THAN = '>='
    OPERATOR_LOWER_THAN = '<'
    OPERATOR_LOWER_OR_EQUALS_THAN = '<='

    def __init__(self):
        self.session: Union[AsyncSession, None] = None
        self.model: Union[DeclarativeBase, None] = None
        self.base_query: Union[Select, None] = None
        self.special_filters = {}

    async def get_all_with_filters(
            self,
            page: int = 1,
            page_size: int = 100,
            filters: Union[List[str], None] = None,
            sorts: Union[List[str], None] = None,
            *args,
            **kwargs
    ):
        """Get all records with pagination, optional filters and sort order."""
        skip = page_size * (page - 1)
        filtered_query = self._get_filtered_query(filters, sorts)

        count_query = select(func.count()).select_from(filtered_query)
        result_query = filtered_query.offset(skip).limit(page_size)

        count = await self.session.execute(count_query)
        count_result = count.scalar_one()

        result = await self.session.execute(result_query)
        records_result = result.scalars().unique().all()

        return {
            "current_page": page,
            "page_size": page_size,
            "number_pages": ceil(count_result / page_size),
            "count": count_result,
            "records": records_result
        }

    def _get_filtered_query(
            self,
            filters: Union[List[str], None] = None,
            sorts: Union[List[str], None] = None
    ):
        """Generates a query with optional filters and sort order."""
        query = self.base_query

        if filters:
            distinct_filters = list(dict.fromkeys(filters))
            processed_filters = self._process_filters(distinct_filters)
            query = query.filter(and_(*processed_filters))

        if sorts:
            processed_sorts = self._process_sorts(sorts)
            query = query.order_by(*processed_sorts)

        return query

    def _process_filters(self, filters: List[str]) -> List[ColumnElement]:
        processed_filters = list()
        for filter_param in filters:
            try:
                key, value = filter_param.split(":", 1)
                #  'key' can be a list of multiple keys, separated by commas;
                #  Multiple keys will be checked as an OR comparison,
                #  against the same value:
                keys = key.split(",")

                sub_queries = []
                for k in keys:
                    if k in self.special_filters:
                        sub_query = self._process_single_special_filter(self.model, k, value)
                    else:
                        sub_query = self._process_single_filter(self.model, k, value)
                    sub_queries.append(sub_query)
                processed_filters.append(or_(*sub_queries))

            except (KeyError, Exception) as _:
                pass

        return processed_filters

    def _process_single_filter(
            self,
            model: DeclarativeBase,
            key: str,
            value: str,
            operator: str = OPERATOR_EQUALS
    ) -> Union[ColumnElement, None]:
        """Generates statements for a single 'key.value' filter

        Parameters:
        key (str): The field to be used in the comparison
        May be a single field or a relationship (in the format 'model.field')

        value (str): The value to be checked against
        Will be cast to a corresponding field type
        """

        model = self._get_model_class(model)

        if key.find(".") == -1:
            field = inspect(model.__dict__[key])

            if isinstance(field.property, sqlalchemy.orm.properties.ColumnProperty):
                return self._get_filter_statement(field, value, operator)

        else:
            rel, skey = key.split(".", 1)
            related = inspect(model.__dict__[rel])

            related_model = related.property.argument
            sub_query = self._process_single_filter(related_model, skey, value)

            # The 'comparator.property.uselist' as True means 'related' is a "to Many" relationship,
            # i.e. related has a collection on the other side.
            # if uselist is True, should use 'any()' instead of 'has()':
            # TODO Both related.any() and related.has() use sub queries, that tend to be slow...
            #  see https://stackoverflow.com/a/8562155/1786389
            if related.comparator.property.uselist:
                return related.any(sub_query)
            else:
                return related.has(sub_query)

    def _process_single_special_filter(
            self,
            model: DeclarativeBase,
            key: str,
            value: str
    ) -> Union[ColumnElement, None]:
        sub_queries = []
        conditions = self.special_filters[key](value)
        for cond in conditions:
            try:
                sub_query = self._process_single_filter(model=model, key=cond[0], value=cond[1], operator=cond[2])
                sub_queries.append(sub_query)
            except (KeyError, Exception) as _:
                pass
        return and_(*sub_queries)

    @staticmethod
    def _get_filter_statement(field: QueryableAttribute, value: Any, operator: str = OPERATOR_EQUALS) -> ColumnElement:
        """Generates a statement for filters

        Uses the correct comparative operator according to the field type
        Assumes 'field.property' is a sqlalchemy.orm.properties.ColumnProperty

        Parameters:
        field (QueryableAttribute): The field to be used in the comparison
        Can be obtained with inspect(SomeModel.__dict__["field_name"])

        value (Any): The value to be checked against
        Will be cast to a corresponding field type; If the value appears to be
        a list, will cast each list item to the corresponding type.

        Returns:
        statement (ColumnElement) the comparative statement
        """
        from sqlalchemy.sql.operators import is_, in_op, ilike_op, gt, ge, lt, le, eq

        value_as_list = value.split(',')
        field_type = field.property.columns[0].type

        # Need to account for sqlalchemy.dialects.postgresql.base fields,
        # because they ARE NOT the same interface of sqlalchemy.sql.sqltypes
        if isinstance(field_type, UUID):
            python_type = uuid
        else:
            python_type = field_type.python_type

        operators = {
            FilteredListDAOMixin.OPERATOR_EQUALS: {"bool": is_, "numeric": in_op, "string": ilike_op, "other": eq},
            FilteredListDAOMixin.OPERATOR_GREATER_THAN: {"bool": None, "numeric": gt, "string": gt, "other": gt},
            FilteredListDAOMixin.OPERATOR_GREATER_OR_EQUALS_THAN: {"bool": None, "numeric": ge, "string": ge,
                                                                   "other": ge},  # NOQA
            FilteredListDAOMixin.OPERATOR_LOWER_THAN: {"bool": None, "numeric": lt, "string": lt, "other": lt},
            FilteredListDAOMixin.OPERATOR_LOWER_OR_EQUALS_THAN: {"bool": None, "numeric": le, "string": le,
                                                                 "other": le},  # NOQA
        }

        # To provide more reliable results, bool values will NOT work as lists:
        if python_type is bool:
            boolean_value = bool(util.strtobool(value))
            return operators[operator]["bool"](cast(field, Boolean), boolean_value)
        elif python_type is int:
            return operators[operator]["numeric"](cast(field, Integer), [int(x) for x in value_as_list])
        elif python_type is float:
            return operators[operator]["numeric"](cast(field, Float), [float(x) for x in value_as_list])
        elif python_type is str:
            statements = []
            for v in value_as_list:
                statements.append(operators[operator]["string"](cast(field, String), "%" + v + "%"))
            return or_(*statements)
        elif python_type is datetime:
            datetime_value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
            return operators[operator]["other"](cast(field, DateTime), datetime_value)

        # by default, filter is converted as a string field:
        return operators[operator]["string"](cast(field, String), [str(x) for x in value_as_list])

    def _process_sorts(self, sorts: List[str]) -> List[UnaryExpression]:
        processed_sorts = list()
        for sort_param in sorts:
            try:
                if sort_param.find(":") == -1:
                    field, direction = sort_param, "ASC"
                else:
                    field, direction = sort_param.split(":", 1)
                exp = self._process_single_sort(self.model, field, direction)
                processed_sorts.append(exp)

            except (KeyError, Exception) as _:
                pass

        return processed_sorts

    def _process_single_sort(self, model: DeclarativeBase, field: str, direction: str) -> Union[UnaryExpression, None]:
        """Generates statements for a single 'field.direction' sort

        Parameters:
        field (str): The field to be used in the sort order
        May be a single field or a relationship (in the format 'model.field')

        direction (str): The direction to be ordered (asc, desc)
        """
        model = self._get_model_class(model)

        if field.find(".") == -1:
            return self._get_sort_statement(model, field, direction)

        else:
            rel, sfield = field.split(".", 1)
            related = inspect(model.__dict__[rel])

            related_model = related.property.argument
            return self._process_single_sort(related_model, sfield, direction)

    @staticmethod
    def _get_sort_statement(model, field, direction):
        if direction.upper() == "DESC":
            return expression.desc(model.__dict__[field])
        return expression.asc(model.__dict__[field])

    def _get_model_class(self, model):
        """Accounts for "forward references", when a related entity is created
        with the class name as  a string instead of a class, like:
        country = relationship("Country")
        """
        if isinstance(model, str):
            module_ = importlib.import_module(self.__module__)
            return getattr(module_, model)
        return model
