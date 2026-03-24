from httpx import AsyncClient

from src.infrastructure.database.seed import CATALOG

# Number of distinct product names in the catalog
_DISTINCT_PRODUCTS = len({item["name"] for item in CATALOG})

# Expected variations count per product, derived from the catalog
_VARIATIONS_PER_PRODUCT = {}
for item in CATALOG:
    _VARIATIONS_PER_PRODUCT.setdefault(item["name"], []).append(item["variation"])


class TestGetMenuStatus:
    async def test_returns_200_with_seeded_catalog(self, seeded_client: AsyncClient):
        response = await seeded_client.get("/menu")
        assert response.status_code == 200

    async def test_returns_200_with_empty_database(self, client: AsyncClient):
        response = await client.get("/menu")
        assert response.status_code == 200


class TestGetMenuResponseShape:
    async def test_response_is_a_list(self, seeded_client: AsyncClient):
        response = await seeded_client.get("/menu")
        assert isinstance(response.json(), list)

    async def test_each_item_has_name_field(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        for item in data:
            assert "name" in item

    async def test_each_item_has_base_price_field(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        for item in data:
            assert "base_price" in item

    async def test_each_item_has_variations_list(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        for item in data:
            assert "variations" in item
            assert isinstance(item["variations"], list)

    async def test_each_variation_has_variation_field(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        for item in data:
            for variation in item["variations"]:
                assert "variation" in variation

    async def test_each_variation_has_price_change_field(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        for item in data:
            for variation in item["variations"]:
                assert "price_change" in variation


class TestGetMenuGrouping:
    async def test_returns_one_item_per_distinct_product_name(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        assert len(data) == _DISTINCT_PRODUCTS

    async def test_no_duplicate_product_names_in_response(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        names = [item["name"] for item in data]
        assert len(names) == len(set(names))

    async def test_all_catalog_product_names_are_present(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        returned_names = {item["name"] for item in data}
        expected_names = {item["name"] for item in CATALOG}
        assert returned_names == expected_names

    async def test_each_product_has_correct_number_of_variations(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        for item in data:
            expected_count = len(_VARIATIONS_PER_PRODUCT[item["name"]])
            assert len(item["variations"]) == expected_count


class TestGetMenuCatalogData:
    async def test_latte_has_correct_base_price(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        latte = next(item for item in data if item["name"] == "Latte")
        assert latte["base_price"] == 4.00

    async def test_latte_has_three_variations(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        latte = next(item for item in data if item["name"] == "Latte")
        assert len(latte["variations"]) == 3

    async def test_latte_variation_names_are_correct(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        latte = next(item for item in data if item["name"] == "Latte")
        variation_names = {v["variation"] for v in latte["variations"]}
        assert variation_names == {"Pumpkin Spice", "Vanilla", "Hazelnut"}

    async def test_espresso_double_shot_price_change(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        espresso = next(item for item in data if item["name"] == "Espresso")
        double_shot = next(v for v in espresso["variations"] if v["variation"] == "Double Shot")
        assert double_shot["price_change"] == 1.00

    async def test_espresso_single_shot_has_zero_price_change(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        espresso = next(item for item in data if item["name"] == "Espresso")
        single_shot = next(v for v in espresso["variations"] if v["variation"] == "Single Shot")
        assert single_shot["price_change"] == 0.00

    async def test_donuts_has_correct_base_price(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        donuts = next(item for item in data if item["name"] == "Donuts")
        assert donuts["base_price"] == 2.00

    async def test_iced_coffee_has_three_variations(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        iced = next(item for item in data if item["name"] == "Iced Coffee")
        assert len(iced["variations"]) == 3


class TestGetMenuEmptyDatabase:
    async def test_returns_empty_list(self, client: AsyncClient):
        data = (await client.get("/menu")).json()
        assert data == []
