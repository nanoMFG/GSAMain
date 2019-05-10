class Recipe:
    def __init__(self, recipe_dict):
        self.recipe = recipe_dict

    def max_temp(self):
        """
        Find the maximum furnace temperature across all of the steps
        :param sample:
        :return: The max temperature or zero if there are no listed steps
        """
        step_temps = [step["furnace_temperature"]["value"] for step in
                      self.preparation_steps if step["furnace_temperature"]["value"]]

        if (len(step_temps)):
            return max(step_temps)
        else:
            return None

    def carbon_source(self):

        list_of_sources = [step["carbon_source"]["value"] for step
                          in self.preparation_steps
                          if step["carbon_source"]["value"] and step["name"]["value"]=='Growing']
        if len(list_of_sources):
            return list_of_sources[0]
        else:
            return None


    @property
    def properties(self):
        return self.recipe['properties']

    @property
    def authors(self):
        return self.recipe['authors']

    @property
    def experiment_year(self):
        return self.recipe['experiment_date'][0]

    def __getattr__(self, k):
        # we don't need a special call to super here because getattr is only
        # called when an attribute is NOT found in the instance's dictionary
        try:
            if isinstance(self.recipe['recipe'][k],dict):
                return self.recipe['recipe'][k]["value"]
            else:
                return self.recipe['recipe'][k]
        except KeyError:
            raise AttributeError
