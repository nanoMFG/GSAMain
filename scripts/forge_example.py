from mdf_forge.forge import Forge
# You don't have to use the name "mdf" but we do for consistency.
mdf = Forge("mdf-test")

def catalysts(datasets):
   return set(map(lambda dataset: dataset["projects"]["nanomfg"]["catalyst"],
                  datasets))

mdf.match_field("projects.nanomfg.catalyst","*")
rslt= mdf.search()
print(len(rslt))
print("Unique catalysts: "+str(catalysts(rslt)))

mdf.match_range("projects.nanomfg.max_temperature", 0, 1000)
res = mdf.search()
print(len(res))