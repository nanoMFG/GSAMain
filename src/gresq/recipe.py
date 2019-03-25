class Recipe:
    def __init__(self, recipe_dict):
        self.recipe = recipe_dict

    def max_temp(self):
        """
        Find the maximum furnace temperature across all of the steps
        :param sample:
        :return: The max temperature or zero if there are no listed steps
        """
        step_temps = list(
            filter(None, list(map(lambda step: step.furnace_temperature,
                                  self.recipe.annealing_steps)) + \
                   list(map(lambda step: step.furnace_temperature,
                            self.recipe.growing_steps)) + \
                   list(map(lambda step: step.furnace_temperature,
                            self.recipe.cooling_steps))))

        if (len(step_temps)):
            return max(step_temps)
        else:
            return 0

    def carbon_source(self):
        if self.recipe.growing_steps:
            list_of_sources = list(filter(None, list(map(lambda step: step.carbon_source, self.recipe.growing_steps))))
            if len(list_of_sources):
                return list_of_sources[0]
            else:
                return ""
            return list(filter(None, list(map(lambda step: step.carbon_source, sample.growing_steps))))[0]
        else:
            return ""

    def __getattr__(self, k):
        # we don't need a special call to super here because getattr is only
        # called when an attribute is NOT found in the instance's dictionary
        try:
            return self.recipe[k]
        except KeyError:
            raise AttributeError
