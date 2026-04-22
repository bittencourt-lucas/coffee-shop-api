from httpx import AsyncClient

from src.infrastructure.database.seed import CATALOG

_DISTINCT_PRODUCTS = len({item["name"] for item in CATALOG})

_VARIATIONS_PER_PRODUCT: dict[str, list[str]] = {}
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
    async def test_response_has_items_field(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        assert "items" in data

    async def test_response_has_pagination_fields(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    async def test_items_is_a_list(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        assert isinstance(data["items"], list)

    async def test_each_item_has_name_field(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        for item in data["items"]:
            assert "name" in item

    async def test_each_item_has_base_price_field(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        for item in data["items"]:
            assert "base_price" in item

    async def test_each_item_has_variations_list(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        for item in data["items"]:
            assert "variations" in item
            assert isinstance(item["variations"], list)

    async def test_each_variation_has_id_field(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        for item in data["items"]:
            for variation in item["variations"]:
                assert "id" in variation

    async def test_each_variation_has_variation_field(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        for item in data["items"]:
            for variation in item["variations"]:
                assert "variation" in variation

    async def test_each_variation_has_unit_price_field(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        for item in data["items"]:
            for variation in item["variations"]:
                assert "unit_price" in variation


class TestGetMenuGrouping:
    async def test_returns_one_item_per_distinct_product_name(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        assert len(data["items"]) == _DISTINCT_PRODUCTS

    async def test_no_duplicate_product_names_in_response(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        names = [item["name"] for item in data["items"]]
        assert len(names) == len(set(names))

    async def test_all_catalog_product_names_are_present(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        returned_names = {item["name"] for item in data["items"]}
        expected_names = {item["name"] for item in CATALOG}
        assert returned_names == expected_names

    async def test_each_product_has_correct_number_of_variations(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        for item in data["items"]:
            expected_count = len(_VARIATIONS_PER_PRODUCT[item["name"]])
            assert len(item["variations"]) == expected_count


class TestGetMenuCatalogData:
    async def test_latte_has_correct_base_price(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        latte = next(item for item in data["items"] if item["name"] == "Latte")
        assert latte["base_price"] == "4.00"

    async def test_latte_has_three_variations(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        latte = next(item for item in data["items"] if item["name"] == "Latte")
        assert len(latte["variations"]) == 3

    async def test_latte_variation_names_are_correct(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        latte = next(item for item in data["items"] if item["name"] == "Latte")
        variation_names = {v["variation"] for v in latte["variations"]}
        assert variation_names == {"Pumpkin Spice", "Vanilla", "Hazelnut"}

    async def test_espresso_double_shot_unit_price(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        espresso = next(item for item in data["items"] if item["name"] == "Espresso")
        double_shot = next(v for v in espresso["variations"] if v["variation"] == "Double Shot")
        assert double_shot["unit_price"] == "3.50"

    async def test_espresso_single_shot_unit_price(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        espresso = next(item for item in data["items"] if item["name"] == "Espresso")
        single_shot = next(v for v in espresso["variations"] if v["variation"] == "Single Shot")
        assert single_shot["unit_price"] == "2.50"

    async def test_donuts_has_correct_base_price(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        donuts = next(item for item in data["items"] if item["name"] == "Donuts")
        assert donuts["base_price"] == "2.00"

    async def test_iced_coffee_has_three_variations(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        iced = next(item for item in data["items"] if item["name"] == "Iced Coffee")
        assert len(iced["variations"]) == 3


class TestGetMenuPagination:
    async def test_default_page_is_1(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        assert data["page"] == 1

    async def test_default_page_size_is_20(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        assert data["page_size"] == 20

    async def test_total_equals_distinct_product_names(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu")).json()
        assert data["total"] == _DISTINCT_PRODUCTS

    async def test_page_param_is_reflected_in_response(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu?page=2&page_size=2")).json()
        assert data["page"] == 2
        assert data["page_size"] == 2

    async def test_beyond_last_page_returns_empty_items(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu?page=999&page_size=20")).json()
        assert data["items"] == []

    async def test_page_size_limits_items_returned(self, seeded_client: AsyncClient):
        data = (await seeded_client.get("/menu?page=1&page_size=2")).json()
        assert len(data["items"]) <= 2


class TestGetMenuEmptyDatabase:
    async def test_returns_empty_items_list(self, client: AsyncClient):
        data = (await client.get("/menu")).json()
        assert data["items"] == []

    async def test_returns_zero_total(self, client: AsyncClient):
        data = (await client.get("/menu")).json()
        assert data["total"] == 0
