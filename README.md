# Sqlalchemy Filter
Filtered/paginated lists on DTO classes using SQLAlchemy

# Installation
```bash
pip install git+https://github.com/rahenrique/sqlalchemy-filter.git
```

# Usage

Create a DTO Class to handle your data retrieving methods. In the following 
example, we are creating a MyModel model, and a corresponding MyModelDTO 
repository class. In the repository class, we are extending from the 
`FilteredListDTOMixin`, to inherit the `get_all_with_filters` method.

```python
from sqlalchemyfilter import FilteredListDTOMixin
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession


class MyModel(DeclarativeBase):
    __tablename__ = "my_models"
    id = Column(Integer, primary_key=True, index=True)
    name_field = Column(String(30), nullable=False)


class MyModelDTO(FilteredListDTOMixin):
    """MyModel data transfer object implementation."""
    
    def __init__(self, session: AsyncSession) -> None:
    super().__init__()
    self.session = session
    self.model = MyModel
    self.base_query = select(MyModel)
```

Later on, in a service or router class, we can query the repository to get the 
list of records using filters and pagination out of the box:
```python
result = await MyModelDTO(session).get_all_with_filters(
        page=1,
        page_size=10,
        filters=["name_field:ABC"],
        sorts=["id:desc"]
```

The response will be something like:
```python
{
    "current_page": 1,
    "page_size": 10,
    "number_pages": 5,
    "count": 42,
    "records": []
}
```

## Common filters

```python
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
        page: int = Query(1, title="Page", description="The requested page"), # NOQA
        page_size: int = Query(100, title="Page size", description=PAGE_SIZE_DESC), # NOQA
        filters: List[str] = Query(list(), title="Filter fields", description=FILTERS_DESC), # NOQA
        sorts: List[str] = Query(list(), title="Sort fields", description=SORTS_DESC) # NOQA
) -> dict:
    return {
        "page": page,
        "page_size": page_size,
        "filters": filters,
        "sorts": sorts
    }
```
