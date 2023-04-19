from typing import List

from sqlalchemy.orm import Query

PAGE_SIZE_DESC = "The max quantity of records to be returned in a single page"
FILTERS_DESC = """This filter can accept search query's like `key:value` and 
will split on the `:` char.<br/><br/>
**key:** If it detects one `.` char inside the `key` 
element (like `name:ABC`), it will treat `key` as a relationship. If it 
detects one or more `,` char inside the `key` element (like `name,code:abc`), 
it will treat `key` as a list of fields, like an `or` comparison.<br/><br/>
**value:** If it detects one `,` char inside the `value` element (like 
`name:AB,XZ`), it will treat `value` as a list of values, like an `or` 
comparison.<br/><br/>
Multiple filters in different fields are joined as `and` conditions;<br>
Multiple values in the same field are joined as `or` conditions."""
SORTS_DESC = """The sort will accept parameters like `col:ASC` or `col:DESC` 
and will split on the `:` char. 
If it does not find a `:` it will sort ascending on that column."""


async def common_filter_parameters(
        page: int = Query(1, title="Page", description="The requested page"),
        page_size: int = Query(100, title="Page size", description=PAGE_SIZE_DESC),
        filters: List[str] = Query(list(), title="Filter fields", description=FILTERS_DESC),
        sorts: List[str] = Query(list(), title="Sort fields", description=SORTS_DESC)
) -> dict:
    """Provides a common filter dictionary to be used in routes as FastAPI Dependencies in path operation decorators.
    The description of each field can be used as Swagger documentation.
    """
    return {
        "page": page,
        "page_size": page_size,
        "filters": filters,
        "sorts": sorts
    }
