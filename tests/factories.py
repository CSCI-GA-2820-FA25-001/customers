"""
Test Factory to make fake objects for testing
"""

import factory
from service.models import Customer


class CustomerFactory(factory.Factory):
    """Creates fake pets that you don't have to feed"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Customer

    id = factory.Sequence(lambda n: n)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    address = factory.Faker("address")

    # Todo: Add your other attributes here...
