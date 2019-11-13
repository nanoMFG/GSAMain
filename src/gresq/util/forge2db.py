from mdf_forge.forge import Forge
from gresq.database.models import MdfForge


def build_db(session):
    mdf = Forge("mdf-test")
    mdf.match_field("projects.nanomfg.catalyst", "*")
    rslt = mdf.search()

    def safe_get_recipe_value(recipe, property):
        if property in recipe and recipe[property]:
            return recipe[property]
        else:
            return None

    for recipe in rslt:
        r = MdfForge()
        r.mdf_id = recipe["mdf"]["mdf_id"]
        r.title = recipe["dc"]["titles"][0]["title"]
        recipe_data = recipe["projects"]["nanomfg"]
        r.base_pressure = recipe_data["base_pressure"]
        r.carbon_source = recipe_data["carbon_source"]
        r.catalyst = recipe_data["catalyst"]
        r.grain_size = safe_get_recipe_value(recipe_data, "grain_size")
        r.max_temperature = recipe_data["max_temperature"]
        r.orientation = safe_get_recipe_value(recipe_data, "orientation")
        r.sample_surface_area = safe_get_recipe_value(
            recipe_data, "sample_surface_area"
        )
        r.sample_thickness = safe_get_recipe_value(recipe_data, "sample_thickness")
        session.add(r)
    session.commit()
