# SQLAlchemyFilter
Filtered/paginated lists on DTO classes using SQLAlchemy.

> This library was built with a specific use case in mind. Because of that, 
> the structure required for this lib to work in a project is too 
> opinionated for a general use out of the box. If this is the case for you, 
> Feel free to fork this repository and make all the changes you need, using 
> this approach as a starting point.

# Installation
```bash
pip install git+https://github.com/rahenrique/sqlalchemy-filter.git
```

To remove the lib, run the following:
```bash
pip uninstall sqlalchemyfilter
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

## Common filters, FastAPI Dependencies and documentation

If you are using FastAPI, there is a Dependency helper to allow you to define 
parameters for filtering and ordering your lists in your API routes:
```python
from sqlalchemyfilter import common_filter_parameters
```

Following is a simple example of how to use this utility in a router file with 
FastAPI:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemyfilter import common_filter_parameters

router = APIRouter()

@router.get("/api/v1/my-models")
async def get_my_models(
        filter_parameters: dict = Depends(common_filter_parameters)
        session: AsyncSession):

    return await MyModelDTO(session).get_all_with_filters(
        page=filter_parameters.get("page"),
        page_size=filter_parameters.get("page_size"),
        filters=filter_parameters.get("filters"),
        sorts=filter_parameters.get("sorts"))
```
