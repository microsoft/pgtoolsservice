from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class PGTSBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
