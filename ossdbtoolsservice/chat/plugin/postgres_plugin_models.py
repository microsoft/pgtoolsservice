from enum import Enum


class ValidationReason(str, Enum):
    # Schema-derived
    MATCHES_COLUMN_ENUM = "Matches a known enum or distinct set of values in the column"
    MATCHES_FOREIGN_KEY = "Matches a value from the referenced foreign key table"
    MATCHES_DATA_DISTRIBUTION = (
        "Matches a frequent or common value in the column that has been previously seen, "
        "not just from the user's casual input."
    )

    # External knowledge
    KNOWN_STANDARD_FORMAT = "Conforms to a known standard format (e.g., ISO country code). "
    "Only applicable if it is known that the column utilizes the standard format."
    USER_CONFIRMED = "Explicitly confirmed by the user"
    MODEL_CONFIDENT_MAPPING = (
        "Model mapped a variant value to its canonical form with high confidence"
    )

    # Contextual validation
    SIMILAR_TO_EXISTING_VALUE = (
        "Semantically or lexically similar to known values in the column"
    )
    VALIDATED_VIA_LOOKUP = "Confirmed via prior query result or dictionary/table lookup"
    DEFAULT_OR_CONFIGURED_VALUE = "Derived from system default, app config, or common default"

    def __str__(self) -> str:
        return self.value
